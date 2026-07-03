"""
OPC UA 订阅制采集：按 endpoint 共享长连接，MonitoredItem 分批订阅并设上限。

大屏/实时监控通过 read_opcua_nodes(data_source_id=...) 读缓存；
管理端「测试连接」仍走一次性直连读（connection_test_services._read_opcua_nodes_direct）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Iterable

from django.conf import settings

from .connection_test_services import (
    OPCUA_TCP_PROBE_TIMEOUT_SECONDS,
    OpcUaNodeReadItem,
    OpcUaReadResult,
    _describe_exception,
    _normalize_opcua_nodes,
    _parse_opcua_endpoint,
    _tcp_probe,
    node_subscribe_enabled,
    nodes_for_opcua_connection,
)


logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = 30
OFFLINE_RETRY_SECONDS = 2.0


def _endpoint_key(connection_config: dict) -> str:
    endpoint = (connection_config.get("endpointUrl") or "").strip().lower()
    username = (connection_config.get("username") or "").strip()
    return f"{endpoint}|{username}"


def _max_monitored_items_per_subscription() -> int:
    return max(1, int(getattr(settings, "OPCUA_MAX_MONITORED_ITEMS_PER_SUBSCRIPTION", 32)))


def _max_monitored_items_per_endpoint() -> int:
    return max(1, int(getattr(settings, "OPCUA_MAX_MONITORED_ITEMS_PER_ENDPOINT", 96)))


def _chunked(items: list, size: int) -> Iterable[list]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _config_fingerprint(connection_config: dict, source_nodes: dict[int, list[dict]]) -> str:
    canonical = {
        "endpoint": (connection_config.get("endpointUrl") or "").strip(),
        "username": (connection_config.get("username") or "").strip(),
        "sources": {
            str(source_id): nodes
            for source_id, nodes in sorted(source_nodes.items(), key=lambda item: item[0])
        },
    }
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _publishing_interval_ms() -> float:
    return float(getattr(settings, "OPCUA_SUBSCRIPTION_PUBLISHING_MS", 500))


@dataclass
class _CachedNode:
    value: str = "-"
    ok: bool = False
    error: str = ""
    updated_at: float = 0.0


@dataclass
class _SourceRegistration:
    data_source_id: int
    connection_config: dict
    node_items: list[dict]


@dataclass
class _EndpointCache:
    endpoint_key: str
    endpoint: str = ""
    source_info: str = ""
    offline: bool = True
    offline_message: str = ""
    node_comments: dict[str, str] = field(default_factory=dict)
    nodes: dict[str, _CachedNode] = field(default_factory=dict)
    connected_at: float = 0.0


class _OpcUaSubHandler:
    def __init__(self, worker: "_OpcUaEndpointWorker") -> None:
        self._worker = worker

    def datachange_notification(self, node, val, data) -> None:  # noqa: ARG002
        try:
            node_id = node.nodeid.to_string()
        except Exception:
            node_id = str(node)
        self._worker._on_datachange(node_id, val)

    def event_notification(self, event) -> None:  # noqa: ARG002
        return


class _OpcUaEndpointWorker:
    """同一 OPC UA endpoint 只建一条连接，多数据源共享 MonitoredItem 配额。"""

    def __init__(self, endpoint_key: str, connection_config: dict) -> None:
        self.endpoint_key = endpoint_key
        self.connection_config = dict(connection_config or {})
        self.publishing_ms = _publishing_interval_ms()
        self._sources: dict[int, list[dict]] = {}
        self._source_comments: dict[int, dict[str, str]] = {}
        self._fingerprint = ""

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._cache = _EndpointCache(endpoint_key=endpoint_key)

    def register_source(
        self,
        data_source_id: int,
        connection_config: dict,
        node_items: list[dict],
    ) -> bool:
        """注册/更新数据源；节点集合变化时返回 True 表示需要重连。"""
        self.connection_config = dict(connection_config or self.connection_config)
        comments = {item["nodeId"]: item.get("comment") or item["nodeId"] for item in node_items}
        with self._lock:
            old_nodes = self._sources.get(data_source_id)
            self._sources[data_source_id] = list(node_items)
            self._source_comments[data_source_id] = comments
            for node_id, comment in comments.items():
                self._cache.node_comments.setdefault(node_id, comment)
            new_fingerprint = _config_fingerprint(self.connection_config, self._sources)
            changed = new_fingerprint != self._fingerprint
            self._fingerprint = new_fingerprint
            if old_nodes is None:
                changed = True
        return changed

    def unregister_source(self, data_source_id: int) -> bool:
        with self._lock:
            self._sources.pop(data_source_id, None)
            self._source_comments.pop(data_source_id, None)
            if not self._sources:
                return True
            self._fingerprint = _config_fingerprint(self.connection_config, self._sources)
            return True

    def has_sources(self) -> bool:
        with self._lock:
            return bool(self._sources)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"opcua-ep-{self.endpoint_key[:48]}",
            daemon=True,
        )
        self._thread.start()

    def stop(self, *, timeout: float = 8.0) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _unique_node_items(self, *, subscribe_only: bool = False) -> list[dict]:
        with self._lock:
            merged: dict[str, dict] = {}
            for items in self._sources.values():
                for item in items:
                    if subscribe_only and not node_subscribe_enabled(item):
                        continue
                    node_id = item["nodeId"]
                    if node_id not in merged:
                        merged[node_id] = item
            nodes = list(merged.values())
            if not subscribe_only:
                return nodes
            cap = _max_monitored_items_per_endpoint()
            if len(nodes) > cap:
                logger.warning(
                    "OPC UA endpoint %s: %d subscribe nodes configured, subscribing first %d (OPCUA_MAX_MONITORED_ITEMS_PER_ENDPOINT)",
                    self.endpoint_key,
                    len(nodes),
                    cap,
                )
                skipped = nodes[cap:]
                nodes = nodes[:cap]
                for item in skipped:
                    self._mark_node_error(item["nodeId"], "超出 endpoint 订阅上限，未订阅")
            return nodes

    def _mark_node_error(self, node_id: str, message: str) -> None:
        with self._lock:
            entry = self._cache.nodes.setdefault(node_id, _CachedNode())
            entry.ok = False
            entry.value = "-"
            entry.error = message
            entry.updated_at = time.time()

    def _on_datachange(self, node_id: str, val) -> None:
        with self._lock:
            entry = self._cache.nodes.setdefault(node_id, _CachedNode())
            entry.value = str(val)
            entry.ok = True
            entry.error = ""
            entry.updated_at = time.time()
            self._cache.offline = False
            self._cache.offline_message = ""

    def _set_offline(self, message: str) -> None:
        with self._lock:
            self._cache.offline = True
            self._cache.offline_message = message

    def _run_loop(self) -> None:
        reconnect_delay = max(1.0, float(getattr(settings, "OPCUA_SUBSCRIPTION_RECONNECT_SECONDS", 2)))
        while not self._stop.is_set():
            try:
                self._connect_subscribe_and_hold()
            except Exception as exc:  # noqa: BLE001
                logger.warning("opcua endpoint worker %s error: %s", self.endpoint_key, exc)
                self._set_offline(_describe_exception(exc))
            if self._stop.wait(reconnect_delay):
                break

    def _connect_subscribe_and_hold(self) -> None:
        if not self.has_sources():
            return

        endpoint = (self.connection_config.get("endpointUrl") or "").strip()
        username = (self.connection_config.get("username") or "").strip()
        password = self.connection_config.get("password") or ""
        offline_retry = max(
            0.5,
            float(getattr(settings, "OPCUA_SUBSCRIPTION_OFFLINE_RETRY_SECONDS", OFFLINE_RETRY_SECONDS)),
        )

        if not endpoint or not endpoint.startswith("opc.tcp://"):
            self._set_offline("OPC UA 服务器地址无效")
            time.sleep(offline_retry)
            return

        host, port = _parse_opcua_endpoint(endpoint)
        if not host:
            self._set_offline(f"无法从 {endpoint} 解析主机名")
            time.sleep(offline_retry)
            return

        tcp_error = _tcp_probe(host, port, timeout=OPCUA_TCP_PROBE_TIMEOUT_SECONDS)
        if tcp_error:
            self._set_offline(tcp_error)
            time.sleep(offline_retry)
            return

        try:
            from asyncua.sync import Client  # type: ignore
        except ImportError:
            self._set_offline("未安装 asyncua，无法建立 OPC UA 订阅")
            time.sleep(30)
            return

        timeout = int(getattr(settings, "OPCUA_SUBSCRIPTION_CLIENT_TIMEOUT_SECONDS", 5))
        client = Client(url=endpoint, timeout=timeout)
        if username:
            client.set_user(username)
            client.set_password(password or "")

        try:
            client.connect()
        except Exception as exc:  # noqa: BLE001
            self._set_offline(f"OPC UA 连接失败: {_describe_exception(exc)}")
            time.sleep(offline_retry)
            return

        subscriptions: list = []
        try:
            source_info = f"{host}:{port}"
            try:
                server_node = client.get_server_node()
                product_uri = server_node.get_child(["0:ServerStatus", "0:BuildInfo", "0:ProductUri"])
                source_info = str(product_uri.read_value() or source_info)
            except Exception:
                pass

            with self._lock:
                self._cache.endpoint = endpoint
                self._cache.source_info = source_info
                self._cache.connected_at = time.time()

            all_node_items = self._unique_node_items(subscribe_only=False)
            subscribe_node_items = self._unique_node_items(subscribe_only=True)
            handler = _OpcUaSubHandler(self)
            node_objects: list = []

            for item in all_node_items:
                node_id = item["nodeId"]
                try:
                    node_obj = client.get_node(node_id)
                    if node_subscribe_enabled(item):
                        node_objects.append(node_obj)
                    value = node_obj.read_value()
                    self._on_datachange(node_id, value)
                except Exception as exc:  # noqa: BLE001
                    self._mark_node_error(node_id, _describe_exception(exc))

            per_sub_limit = _max_monitored_items_per_subscription()
            for chunk in _chunked(node_objects, per_sub_limit):
                if not chunk:
                    continue
                try:
                    subscription = client.create_subscription(self.publishing_ms, handler)
                    subscription.subscribe_data_change(chunk)
                    subscriptions.append(subscription)
                except Exception as exc:  # noqa: BLE001
                    err = _describe_exception(exc)
                    logger.warning(
                        "opcua endpoint %s: subscribe chunk (%d nodes) failed: %s",
                        self.endpoint_key,
                        len(chunk),
                        err,
                    )
                    for node_obj in chunk:
                        try:
                            node_id = node_obj.nodeid.to_string()
                        except Exception:
                            node_id = str(node_obj)
                        if "BadTooManyMonitoredItems" in err or "TooManyMonitoredItems" in err:
                            self._mark_node_error(node_id, "服务器 MonitoredItem 已达上限")
                        else:
                            self._mark_node_error(node_id, f"订阅失败: {err}")

            with self._lock:
                if self._cache.nodes and any(n.ok for n in self._cache.nodes.values()):
                    self._cache.offline = False
                    self._cache.offline_message = ""
                elif not all_node_items:
                    self._cache.offline = True
                    self._cache.offline_message = "未配置可订阅节点"

            while not self._stop.is_set():
                time.sleep(1)
        finally:
            for subscription in subscriptions:
                try:
                    subscription.delete()
                except Exception:  # noqa: BLE001
                    pass
            try:
                client.disconnect()
            except Exception:  # noqa: BLE001
                pass

    def build_read_result(self, data_source_id: int, node_items: list[dict]) -> OpcUaReadResult:
        with self._lock:
            cache = self._cache
            source_comments = self._source_comments.get(data_source_id, {})
            if cache.offline and not cache.nodes:
                return OpcUaReadResult(
                    ok=False,
                    offline=True,
                    message=cache.offline_message or "订阅未就绪",
                    endpoint=cache.endpoint or (self.connection_config.get("endpointUrl") or ""),
                    source_info=cache.source_info or "",
                    items=[],
                )

            items: list[OpcUaNodeReadItem] = []
            for spec in node_items:
                node_id = spec["nodeId"]
                comment = spec.get("comment") or source_comments.get(node_id) or cache.node_comments.get(node_id) or node_id
                cached = cache.nodes.get(node_id)
                if cached and cached.ok:
                    items.append(
                        OpcUaNodeReadItem(
                            comment=comment,
                            node_id=node_id,
                            ok=True,
                            value=cached.value,
                        )
                    )
                elif cached:
                    items.append(
                        OpcUaNodeReadItem(
                            comment=comment,
                            node_id=node_id,
                            ok=False,
                            value="-",
                            error=cached.error or "订阅读点失败",
                        )
                    )
                else:
                    items.append(
                        OpcUaNodeReadItem(
                            comment=comment,
                            node_id=node_id,
                            ok=False,
                            value="-",
                            error="等待首次读取" if not node_subscribe_enabled(spec) else "等待订阅数据",
                        )
                    )

            all_ok = len(items) > 0 and all(item.ok for item in items)
            return OpcUaReadResult(
                ok=all_ok,
                offline=cache.offline,
                message="订阅缓存读取" if not cache.offline else (cache.offline_message or "订阅离线"),
                endpoint=cache.endpoint or (self.connection_config.get("endpointUrl") or ""),
                source_info=cache.source_info or "",
                items=items,
            )


class OpcUaSubscriptionManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._endpoint_workers: dict[str, _OpcUaEndpointWorker] = {}
        self._source_registrations: dict[int, _SourceRegistration] = {}
        self._source_endpoint: dict[int, str] = {}
        self._started = False
        self._reconcile_thread: threading.Thread | None = None
        self._wake = threading.Event()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
        self._reconcile_thread = threading.Thread(
            target=self._reconcile_loop,
            name="opcua-sub-reconcile",
            daemon=True,
        )
        self._reconcile_thread.start()
        logger.info("OPC UA subscription manager started (lazy per-source subscribe)")

    def schedule_sync(self) -> None:
        self._wake.set()

    def sync_from_database(self) -> None:
        """仅清理已禁用数据源，并刷新已激活订阅的配置；不自动订阅全部启用源。"""
        from .models import DataSourceConfig

        enabled_ids = set(
            DataSourceConfig.objects.filter(is_enabled=True, source_type="opcua").values_list("pk", flat=True)
        )
        for data_source_id in list(self._source_registrations.keys()):
            if data_source_id not in enabled_ids:
                self._stop_source(data_source_id)

        if not self._source_registrations:
            return

        qs = DataSourceConfig.objects.filter(
            pk__in=list(self._source_registrations.keys()),
            is_enabled=True,
            source_type="opcua",
        ).only("id", "connection_config", "node")
        for ds in qs:
            node_items = nodes_for_opcua_connection(_normalize_opcua_nodes(ds.node, ds.connection_config or {}))
            self._ensure_worker(ds.pk, ds.connection_config or {}, node_items)

    def _ensure_worker(
        self,
        data_source_id: int,
        connection_config: dict,
        node_items: list[dict],
    ) -> None:
        endpoint_key = _endpoint_key(connection_config)
        old_endpoint_key = self._source_endpoint.get(data_source_id)
        if old_endpoint_key and old_endpoint_key != endpoint_key:
            self._stop_source(data_source_id)

        registration = _SourceRegistration(
            data_source_id=data_source_id,
            connection_config=dict(connection_config or {}),
            node_items=list(node_items),
        )
        self._source_registrations[data_source_id] = registration
        self._source_endpoint[data_source_id] = endpoint_key

        worker = self._endpoint_workers.get(endpoint_key)
        if worker is None:
            worker = _OpcUaEndpointWorker(endpoint_key, connection_config)
            self._endpoint_workers[endpoint_key] = worker

        needs_restart = worker.register_source(data_source_id, connection_config, node_items)
        if needs_restart and worker._thread and worker._thread.is_alive():  # noqa: SLF001
            worker.stop()
        worker.start()

    def _stop_source(self, data_source_id: int) -> None:
        self._source_registrations.pop(data_source_id, None)
        endpoint_key = self._source_endpoint.pop(data_source_id, None)
        if not endpoint_key:
            return
        worker = self._endpoint_workers.get(endpoint_key)
        if not worker:
            return
        should_stop = worker.unregister_source(data_source_id)
        if should_stop or not worker.has_sources():
            worker.stop()
            self._endpoint_workers.pop(endpoint_key, None)
        elif worker._thread and worker._thread.is_alive():  # noqa: SLF001
            worker.stop()
            worker.start()

    def _reconcile_loop(self) -> None:
        interval = max(10, int(getattr(settings, "OPCUA_SUBSCRIPTION_RECONCILE_SECONDS", RECONCILE_INTERVAL_SECONDS)))
        while True:
            self._wake.wait(interval)
            self._wake.clear()
            try:
                self.sync_from_database()
            except Exception:  # noqa: BLE001
                logger.exception("opcua subscription reconcile failed")

    def read(
        self,
        data_source_id: int,
        connection_config: dict,
        node,
        *,
        history=None,
    ) -> OpcUaReadResult:
        node_items = nodes_for_opcua_connection(_normalize_opcua_nodes(node, connection_config))
        self._ensure_worker(data_source_id, connection_config, node_items)

        endpoint_key = self._source_endpoint.get(data_source_id)
        worker = self._endpoint_workers.get(endpoint_key) if endpoint_key else None
        result = worker.build_read_result(data_source_id, node_items) if worker else OpcUaReadResult(
            ok=False,
            offline=True,
            message="订阅 worker 未启动",
            endpoint=(connection_config.get("endpointUrl") or ""),
            source_info="",
            items=[],
        )

        if history is not None:
            try:
                from .opcua_history_services import persist_opcua_read

                persist_opcua_read(result, history, duration_ms=0)
            except Exception:  # noqa: BLE001
                logger.exception("opc ua history persist failed (subscription read)")

        return result


_manager: OpcUaSubscriptionManager | None = None
_manager_lock = threading.Lock()


def get_opcua_subscription_manager() -> OpcUaSubscriptionManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = OpcUaSubscriptionManager()
        return _manager


def start_opcua_subscription_manager() -> None:
    get_opcua_subscription_manager().start()


def notify_opcua_subscription_config_changed() -> None:
    mgr = get_opcua_subscription_manager()
    if not mgr._started:  # noqa: SLF001
        mgr.start()
    else:
        mgr.schedule_sync()


def prewarm_opcua_data_sources(source_ids: list[int] | None) -> None:
    """在大屏读缓存前启动对应 OPC UA 订阅 worker，避免首屏阻塞等待。"""
    if not source_ids:
        return

    from .models import DataSourceConfig

    mgr = get_opcua_subscription_manager()
    if not mgr._started:  # noqa: SLF001
        mgr.start()

    qs = DataSourceConfig.objects.filter(
        pk__in=list(source_ids),
        is_enabled=True,
        source_type="opcua",
    ).only("id", "connection_config", "node")
    for ds in qs:
        node_items = nodes_for_opcua_connection(_normalize_opcua_nodes(ds.node, ds.connection_config or {}))
        mgr._ensure_worker(ds.pk, ds.connection_config or {}, node_items)  # noqa: SLF001
