"""Real connection-testing helpers for data source configurations.

The ``database`` and ``opcua`` source types perform an actual network probe
against the target server.  Other source types (Modbus TCP, SAP RFC, 报修系统)
still rely on parameter validation only; extend this module if a real probe
is required for them as well.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import socket
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


TCP_PROBE_TIMEOUT_SECONDS = 5
OPCUA_TCP_PROBE_TIMEOUT_SECONDS = 3
DB_CONNECT_TIMEOUT_SECONDS = 15
DB_READ_TIMEOUT_SECONDS = 15
OPCUA_DEFAULT_PORT = 4840
OPCUA_TIMEOUT_SECONDS = 5


def _looks_like_handshake_failure(message: str) -> bool:
    lowered = message.lower()
    return (
        "lost connection to" in lowered
        or "reading initial communication packet" in lowered
        or "reading authorization packet" in lowered
    )


def _annotate_handshake_error(engine: str, raw: str) -> str:
    return (
        f"{engine} 握手失败: {raw}\n"
        "可能原因：\n"
        " 1) 服务器对客户端 IP 做反向 DNS 解析超时（设置 my.cnf [mysqld] skip-name-resolve）；\n"
        " 2) 客户端在 max_connect_errors 内已多次失败，服务器临时拉黑客户端 IP（执行 FLUSH HOSTS 或重启服务）；\n"
        " 3) 服务器要求 TLS/SSL 而客户端未启用；\n"
        " 4) bind-address 仅监听其它网卡，与本机不通。"
    )

DEFAULT_DATABASE_PORTS = {
    "mysql": 3306,
    "mariadb": 3306,
    "postgresql": 5432,
    "postgres": 5432,
    "sqlserver": 1433,
    "mssql": 1433,
    "oracle": 1521,
}


@dataclass
class ConnectionTestResult:
    ok: bool
    message: str
    detail: Optional[str] = None


@dataclass
class OpcUaNodeReadItem:
    comment: str
    node_id: str
    ok: bool
    value: str
    error: str = ""


@dataclass
class OpcUaReadResult:
    ok: bool
    offline: bool
    message: str
    endpoint: str
    source_info: str
    items: list[OpcUaNodeReadItem]


def _coerce_int(value, default: Optional[int] = None) -> Optional[int]:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _tcp_probe(host: str, port: int, *, timeout: float | None = None) -> Optional[str]:
    """Quickly check that the host/port is reachable.

    Returns ``None`` on success, or a human-readable error string on failure.
    """
    probe_timeout = TCP_PROBE_TIMEOUT_SECONDS if timeout is None else timeout

    try:
        with socket.create_connection((host, port), timeout=probe_timeout):
            return None
    except socket.gaierror as exc:
        return f"无法解析主机 {host}: {exc}"
    except (socket.timeout, TimeoutError):
        return f"连接 {host}:{port} 超时（{probe_timeout}s）"
    except OSError as exc:
        return f"连接 {host}:{port} 失败: {exc}"


def test_database_connection(connection_config: dict) -> ConnectionTestResult:
    engine_raw = (connection_config.get("engine") or "mysql").strip().lower()
    host = (connection_config.get("host") or "").strip()
    database = (connection_config.get("database") or "").strip()
    username = (connection_config.get("username") or "").strip()
    password = connection_config.get("password") or ""
    port = _coerce_int(
        connection_config.get("port"),
        default=DEFAULT_DATABASE_PORTS.get(engine_raw),
    )

    if not host:
        return ConnectionTestResult(False, "数据库主机不能为空")
    if port is None:
        return ConnectionTestResult(False, "数据库端口不能为空")
    if port <= 0 or port > 65535:
        return ConnectionTestResult(False, f"数据库端口 {port} 不合法")

    if engine_raw in ("mysql", "mariadb"):
        return _test_mysql(host, port, username, password, database)
    if engine_raw in ("postgresql", "postgres"):
        return _test_postgresql(host, port, username, password, database)
    if engine_raw in ("sqlserver", "mssql"):
        return _test_sqlserver(host, port, username, password, database)
    if engine_raw == "oracle":
        return _test_oracle(host, port, username, password, database)

    tcp_error = _tcp_probe(host, port)
    if tcp_error:
        return ConnectionTestResult(False, tcp_error)
    return ConnectionTestResult(
        True,
        f"已连通 {host}:{port}（未知数据库类型 {engine_raw}，仅完成 TCP 探测）",
    )


def _test_mysql(host: str, port: int, user: str, password: str, db: str) -> ConnectionTestResult:
    try:
        import MySQLdb  # type: ignore
        from MySQLdb import OperationalError  # type: ignore
    except ImportError:
        tcp_error = _tcp_probe(host, port)
        if tcp_error:
            return ConnectionTestResult(False, tcp_error)
        return ConnectionTestResult(
            True,
            f"已连通 {host}:{port}（未安装 mysqlclient，未执行登录测试）",
        )

    kwargs = {
        "host": host,
        "port": port,
        "user": user,
        "passwd": password,
        "connect_timeout": DB_CONNECT_TIMEOUT_SECONDS,
        "read_timeout": DB_READ_TIMEOUT_SECONDS,
        "write_timeout": DB_READ_TIMEOUT_SECONDS,
        "charset": "utf8mb4",
    }
    if db:
        kwargs["db"] = db

    try:
        conn = MySQLdb.connect(**kwargs)
    except OperationalError as exc:
        raw = str(exc.args[-1] if exc.args else exc)
        if _looks_like_handshake_failure(raw):
            return ConnectionTestResult(False, _annotate_handshake_error("MySQL", raw))
        return ConnectionTestResult(False, f"MySQL 连接失败: {raw}")
    except Exception as exc:  # noqa: BLE001 - surface driver errors verbatim
        raw = str(exc)
        if _looks_like_handshake_failure(raw):
            return ConnectionTestResult(False, _annotate_handshake_error("MySQL", raw))
        return ConnectionTestResult(False, f"MySQL 连接失败: {raw}")

    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
    finally:
        conn.close()
    return ConnectionTestResult(True, f"成功连接 MySQL {host}:{port}")


def _test_postgresql(host: str, port: int, user: str, password: str, db: str) -> ConnectionTestResult:
    try:
        import psycopg2  # type: ignore
    except ImportError:
        try:
            import psycopg  # type: ignore  # psycopg3
            psycopg2 = None
        except ImportError:
            tcp_error = _tcp_probe(host, port)
            if tcp_error:
                return ConnectionTestResult(False, tcp_error)
            return ConnectionTestResult(
                True,
                f"已连通 {host}:{port}（未安装 psycopg2/psycopg，未执行登录测试）",
            )
    else:
        psycopg = None

    try:
        if psycopg2 is not None:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user or None,
                password=password or None,
                dbname=db or None,
                connect_timeout=DB_CONNECT_TIMEOUT_SECONDS,
            )
        else:
            conn = psycopg.connect(  # type: ignore[union-attr]
                host=host,
                port=port,
                user=user or None,
                password=password or None,
                dbname=db or None,
                connect_timeout=DB_CONNECT_TIMEOUT_SECONDS,
            )
    except Exception as exc:  # noqa: BLE001
        return ConnectionTestResult(False, f"PostgreSQL 连接失败: {exc}")

    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
    finally:
        conn.close()
    return ConnectionTestResult(True, f"成功连接 PostgreSQL {host}:{port}")


def _test_sqlserver(host: str, port: int, user: str, password: str, db: str) -> ConnectionTestResult:
    try:
        import pyodbc  # type: ignore
    except ImportError:
        try:
            import pymssql  # type: ignore
        except ImportError:
            tcp_error = _tcp_probe(host, port)
            if tcp_error:
                return ConnectionTestResult(False, tcp_error)
            return ConnectionTestResult(
                True,
                f"已连通 {host}:{port}（未安装 pyodbc/pymssql，未执行登录测试）",
            )
        try:
            conn = pymssql.connect(
                server=host,
                port=port,
                user=user or None,
                password=password or None,
                database=db or None,
                login_timeout=DB_CONNECT_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # noqa: BLE001
            return ConnectionTestResult(False, f"SQL Server 连接失败: {exc}")
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
        finally:
            conn.close()
        return ConnectionTestResult(True, f"成功连接 SQL Server {host}:{port} (pymssql)")

    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not drivers:
        tcp_error = _tcp_probe(host, port)
        if tcp_error:
            return ConnectionTestResult(False, tcp_error)
        return ConnectionTestResult(
            True,
            f"已连通 {host}:{port}（未发现 ODBC SQL Server 驱动，未执行登录测试）",
        )
    driver = drivers[0]
    conn_str = (
        f"DRIVER={{{driver}}};SERVER={host},{port};"
        f"UID={user};PWD={password};Connection Timeout={DB_CONNECT_TIMEOUT_SECONDS};"
    )
    if db:
        conn_str += f"DATABASE={db};"
    try:
        conn = pyodbc.connect(conn_str, timeout=DB_CONNECT_TIMEOUT_SECONDS)
    except Exception as exc:  # noqa: BLE001
        return ConnectionTestResult(False, f"SQL Server 连接失败: {exc}")
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
    finally:
        conn.close()
    return ConnectionTestResult(True, f"成功连接 SQL Server {host}:{port} ({driver})")


def _test_oracle(host: str, port: int, user: str, password: str, db: str) -> ConnectionTestResult:
    driver_module = None
    try:
        import oracledb as driver_module  # type: ignore
    except ImportError:
        try:
            import cx_Oracle as driver_module  # type: ignore
        except ImportError:
            tcp_error = _tcp_probe(host, port)
            if tcp_error:
                return ConnectionTestResult(False, tcp_error)
            return ConnectionTestResult(
                True,
                f"已连通 {host}:{port}（未安装 oracledb/cx_Oracle，未执行登录测试）",
            )

    service = db or "XE"
    dsn = f"{host}:{port}/{service}"
    try:
        conn = driver_module.connect(user=user, password=password, dsn=dsn)
    except Exception as exc:  # noqa: BLE001
        return ConnectionTestResult(False, f"Oracle 连接失败: {exc}")
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM DUAL")
        cur.fetchone()
        cur.close()
    finally:
        conn.close()
    return ConnectionTestResult(True, f"成功连接 Oracle {dsn}")


def _parse_opcua_endpoint(endpoint_url: str) -> tuple[str, int]:
    """Return ``(host, port)`` parsed from an ``opc.tcp://host:port[/path]`` URL."""

    parsed = urlparse(endpoint_url)
    host = parsed.hostname or ""
    port = parsed.port or OPCUA_DEFAULT_PORT
    return host, port


def _opc_node_path_key(node_id: str) -> str:
    """从 nodeId 提取路径键，兼容 ns=2;s= 与 NS2|String| 等格式。"""
    nid = (node_id or "").strip()
    if not nid:
        return ""
    lower = nid.lower()
    if lower.startswith("ns=2;s="):
        return nid[7:]
    if lower.startswith("ns=1;s="):
        return nid[7:]
    if "|" in nid:
        parts = nid.split("|")
        if len(parts) >= 3:
            return parts[-1]
    return nid


# 机床静态信息：连接时读一次即可，不占 MonitoredItem 配额（可被节点 subscribe:false 覆盖）
_OPCUA_READ_ONCE_PATHS = frozenset(
    {
        # 西门子 / 通用
        "/Nck/Configuration/nckVersion",
        "/Nck/Configuration/nckType",
        "/Nck/State/hwProductSerialNr[1]",
        "/Nck/Configuration/maxnumGlobMachAxes",
        "/Nck/Configuration/numGlobMachAxes",
        "/Channel/Configuration/numSpindles[u1, 1]",
        "/Channel/LogicalSpindle/acSmaxVelo[u1, 1]",
        "/Channel/Drive/AXCONF_CHANAX_NAME_TAB[1]",
        # 新代 CNCInterface（NS1）
        "CNCInterface/CncChannelList0/CncChannel1/Id0",
        "CNCInterface/CncSpindleList0/CncSpindle1/IsInactive0",
        "CNCInterface/CncSpindleList0/CncSpindle1/IsVirtual0",
        "CNCInterface/CncSpindleList0/CncSpindle1/ActChannel0",
        "CNCInterface/PowerOnSpan0",
    }
)


def _coerce_subscribe_flag(value) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in ("1", "true", "yes", "subscribe", "sub"):
            return True
        if token in ("0", "false", "no", "once", "read_once", "static"):
            return False
    return None


def node_on_demand_only(node_item: dict) -> bool:
    """按需读取节点：不参与订阅/连接预读（如历史报警列表）。"""
    read_when = (node_item.get("readWhen") or node_item.get("read_when") or "").strip().lower()
    if read_when in {"alarm", "on_alarm", "alarm_only"}:
        return True
    subscribe_raw = node_item.get("subscribe")
    if isinstance(subscribe_raw, str):
        token = subscribe_raw.strip().lower()
        if token in {"on_alarm", "alarm", "alarm_only"}:
            return True
    path_key = _opc_node_path_key(node_item.get("nodeId") or "")
    return path_key in _OPCUA_ON_DEMAND_PATHS


# 历史报警等：仅报警态下直连读取，不占 MonitoredItem、连接时不预读
_OPCUA_ON_DEMAND_PATHS = frozenset(
    {
        "CNCInterface/CurrentAlarm0",
    }
)


def nodes_for_opcua_connection(node_items: list[dict]) -> list[dict]:
    return [item for item in node_items if not node_on_demand_only(item)]


def node_subscribe_enabled(node_item: dict) -> bool:
    """是否对该节点建立 MonitoredItem 订阅；False 表示连接时读一次并缓存。"""
    if node_on_demand_only(node_item):
        return False
    explicit = _coerce_subscribe_flag(node_item.get("subscribe"))
    if explicit is not None:
        return explicit
    path_key = _opc_node_path_key(node_item.get("nodeId") or "")
    if path_key in _OPCUA_READ_ONCE_PATHS:
        return False
    return True


def split_opcua_nodes_by_subscribe(node_items: list[dict]) -> tuple[list[dict], list[dict]]:
    subscribe_items: list[dict] = []
    read_once_items: list[dict] = []
    for item in node_items:
        if node_on_demand_only(item):
            continue
        if node_subscribe_enabled(item):
            subscribe_items.append(item)
        else:
            read_once_items.append(item)
    return subscribe_items, read_once_items


def _normalize_opcua_nodes(node, connection_config: dict) -> list[dict]:
    if isinstance(node, list):
        cleaned = []
        for index, item in enumerate(node, start=1):
            if isinstance(item, dict):
                node_id = (item.get("nodeId") or "").strip() if isinstance(item.get("nodeId"), str) else ""
                comment = (item.get("comment") or "").strip() if isinstance(item.get("comment"), str) else ""
                if node_id and comment:
                    entry = {"nodeId": node_id, "comment": comment}
                    read_when = (item.get("readWhen") or item.get("read_when") or "").strip().lower()
                    subscribe_raw = item.get("subscribe")
                    if isinstance(subscribe_raw, str) and subscribe_raw.strip().lower() in {
                        "on_alarm",
                        "alarm",
                        "alarm_only",
                    }:
                        read_when = read_when or "alarm"
                    if read_when:
                        entry["readWhen"] = read_when
                    if "subscribe" in item:
                        entry["subscribe"] = node_subscribe_enabled({**entry, "subscribe": item.get("subscribe")})
                    else:
                        entry["subscribe"] = node_subscribe_enabled(entry)
                    cleaned.append(entry)
                    continue
            if isinstance(item, str):
                node_id = item.strip()
                if node_id:
                    entry = {"nodeId": node_id, "comment": f"未命名节点{index}"}
                    entry["subscribe"] = node_subscribe_enabled(entry)
                    cleaned.append(entry)
        if cleaned:
            return cleaned
    fallback_node = (connection_config.get("nodeId") or "").strip()
    if fallback_node:
        entry = {"nodeId": fallback_node, "comment": "未命名节点1"}
        entry["subscribe"] = node_subscribe_enabled(entry)
        return [entry]
    return []


def read_opcua_nodes(
    connection_config: dict,
    node=None,
    *,
    history=None,
    data_source_id: int | None = None,
) -> OpcUaReadResult:
    """从 OPC UA 订阅缓存读取节点（须传 data_source_id）。管理端测试连接请用 test_opcua_connection。"""
    if not data_source_id:
        return OpcUaReadResult(
            ok=False,
            offline=True,
            message="缺少 data_source_id，无法读取 OPC UA 订阅缓存",
            endpoint=(connection_config.get("endpointUrl") or ""),
            source_info="",
            items=[],
        )

    from .opcua_subscription_services import get_opcua_subscription_manager

    mgr = get_opcua_subscription_manager()
    if not mgr._started:  # noqa: SLF001
        mgr.start()
    return mgr.read(int(data_source_id), connection_config, node, history=history)


def _read_opcua_nodes_direct(connection_config: dict, node=None, *, history=None) -> OpcUaReadResult:
    """管理端「测试连接」专用：一次性直连读点（非订阅）。"""
    t0 = time.perf_counter()

    def finish(result: OpcUaReadResult) -> OpcUaReadResult:
        if history is not None:
            try:
                from .opcua_history_services import persist_opcua_read

                persist_opcua_read(result, history, int((time.perf_counter() - t0) * 1000))
            except Exception:  # noqa: BLE001
                logger.exception("opc ua history persist failed")
        return result

    endpoint = (connection_config.get("endpointUrl") or "").strip()
    node_items = _normalize_opcua_nodes(node, connection_config)
    username = (connection_config.get("username") or "").strip()
    password = connection_config.get("password") or ""

    if not endpoint:
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message="OPC UA 服务器地址不能为空",
                endpoint=endpoint,
                source_info="",
                items=[],
            )
        )
    if not endpoint.startswith("opc.tcp://"):
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message="OPC UA 服务器地址需以 opc.tcp:// 开头",
                endpoint=endpoint,
                source_info="",
                items=[],
            )
        )

    host, port = _parse_opcua_endpoint(endpoint)
    if not host:
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message=f"无法从 {endpoint} 解析主机名",
                endpoint=endpoint,
                source_info="",
                items=[],
            )
        )

    tcp_error = _tcp_probe(host, port)
    if tcp_error:
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message=tcp_error,
                endpoint=endpoint,
                source_info="",
                items=[],
            )
        )

    try:
        from asyncua.sync import Client  # type: ignore
    except ImportError:
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=False,
                message="未安装 asyncua，无法读取节点实时值",
                endpoint=endpoint,
                source_info=f"{host}:{port}",
                items=[],
            )
        )

    client = Client(url=endpoint, timeout=OPCUA_TIMEOUT_SECONDS)
    if username:
        client.set_user(username)
        client.set_password(password or "")

    try:
        client.connect()
    except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message=f"OPC UA 连接超时（{OPCUA_TIMEOUT_SECONDS}s）",
                endpoint=endpoint,
                source_info=f"{host}:{port}",
                items=[],
            )
        )
    except Exception as exc:  # noqa: BLE001
        return finish(
            OpcUaReadResult(
                ok=False,
                offline=True,
                message=f"OPC UA 连接失败: {_describe_exception(exc)}",
                endpoint=endpoint,
                source_info=f"{host}:{port}",
                items=[],
            )
        )

    items = []
    source_info = f"{host}:{port}"
    try:
        try:
            server_node = client.get_server_node()
            product_uri = server_node.get_child(["0:ServerStatus", "0:BuildInfo", "0:ProductUri"])
            source_info = str(product_uri.read_value() or source_info)
        except Exception:
            source_info = f"{host}:{port}"

        for item in node_items:
            node_id = item["nodeId"]
            comment = item["comment"]
            try:
                node_obj = client.get_node(node_id)
                value = node_obj.read_value()
                items.append(
                    OpcUaNodeReadItem(
                        comment=comment,
                        node_id=node_id,
                        ok=True,
                        value=str(value),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                items.append(
                    OpcUaNodeReadItem(
                        comment=comment,
                        node_id=node_id,
                        ok=False,
                        value="-",
                        error=_describe_exception(exc),
                    )
                )
    finally:
        try:
            client.disconnect()
        except Exception:  # noqa: BLE001
            pass

    all_ok = len(items) > 0 and all(item.ok for item in items)
    return finish(
        OpcUaReadResult(
            ok=all_ok,
            offline=False,
            message="读取完成" if items else "未配置可读取节点",
            endpoint=endpoint,
            source_info=source_info,
            items=items,
        )
    )


def test_opcua_connection(connection_config: dict, node=None, *, history=None) -> ConnectionTestResult:
    """Connect to OPC UA and verify configured nodes in order (direct read, not subscription cache)."""
    result = _read_opcua_nodes_direct(connection_config, node=node, history=history)
    if not result.items:
        return ConnectionTestResult(result.ok, result.message)

    lines = []
    failed = False
    for index, item in enumerate(result.items, start=1):
        if item.ok:
            lines.append(f"{index}. {item.comment} = {item.value}")
        else:
            failed = True
            lines.append(f"{index}. {item.comment} = 获取失败 ({item.error})")
    summary = "\n".join(lines)
    prefix = "成功连接" if not failed and not result.offline else "连接或读取异常"
    return ConnectionTestResult(
        (not failed) and (not result.offline),
        f"{prefix} OPC UA {result.endpoint}（{result.source_info}），节点读取结果（按配置顺序）：\n{summary}",
    )


def _describe_exception(exc: BaseException) -> str:
    """Format an exception so the human-facing message is never empty."""

    cls = exc.__class__.__name__
    text = str(exc).strip()
    if text:
        return f"{cls}: {text}"
    rep = repr(exc).strip()
    if rep in ("", f"{cls}()", f"{cls}('')"):
        return cls
    return f"{cls}: {rep}"


S7_DATA_TYPES = {"bool", "int", "dint", "real", "string"}
S7_TYPE_SIZES = {
    "bool": 1,
    "int": 2,
    "dint": 4,
    "real": 4,
}


def _coerce_int(value, *, field: str, default=None, min_value=None):
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"{field} is required")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{field} must be >= {min_value}")
    return parsed


def _normalize_s7_nodes(node) -> list[dict]:
    if node in (None, {}, []):
        return []
    if not isinstance(node, list):
        raise ValueError("node must be a list for s7 source")

    normalized: list[dict] = []
    for index, item in enumerate(node, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"node item #{index} must be an object")
        comment = item.get("comment")
        if not isinstance(comment, str) or not comment.strip():
            raise ValueError(f"node item #{index} must include non-empty comment")

        db_number = _coerce_int(item.get("dbNumber"), field=f"node item #{index} dbNumber", min_value=1)
        offset = _coerce_int(item.get("offset"), field=f"node item #{index} offset", min_value=0)
        data_type = (item.get("dataType") or "").strip().lower()
        if data_type not in S7_DATA_TYPES:
            raise ValueError(
                f"node item #{index} dataType must be one of: {', '.join(sorted(S7_DATA_TYPES))}"
            )

        bit = None
        length = None
        if data_type == "bool":
            bit = _coerce_int(item.get("bit"), field=f"node item #{index} bit", min_value=0)
            if bit > 7:
                raise ValueError(f"node item #{index} bit must be between 0 and 7")
        elif data_type == "string":
            length = _coerce_int(item.get("length"), field=f"node item #{index} length", min_value=1)

        normalized.append(
            {
                "comment": comment.strip(),
                "db_number": db_number,
                "offset": offset,
                "data_type": data_type,
                "bit": bit,
                "length": length,
            }
        )
    return normalized


def _s7_point_size(point: dict) -> int:
    data_type = point["data_type"]
    if data_type == "string":
        return point["length"]
    return S7_TYPE_SIZES.get(data_type, 1)


def _s7_db_read_ranges(nodes: list[dict]) -> dict[int, tuple[int, int]]:
    ranges: dict[int, tuple[int, int]] = {}
    for point in nodes:
        db_number = point["db_number"]
        start = point["offset"]
        end = start + _s7_point_size(point)
        if db_number not in ranges:
            ranges[db_number] = (start, end)
            continue
        prev_start, prev_end = ranges[db_number]
        ranges[db_number] = (min(prev_start, start), max(prev_end, end))
    return ranges


def _decode_s7_string(raw: bytes) -> str:
    chars = []
    for byte in raw:
        if byte == 0:
            break
        chars.append(chr(byte))
    return "".join(chars)


def _parse_s7_value(data: bytes, point: dict):
    data_type = point["data_type"]
    offset = point["offset"] - point["_read_start"]
    if data_type == "bool":
        from snap7.util import get_bool

        return get_bool(data, offset, point["bit"])
    if data_type == "int":
        from snap7.util import get_int

        return get_int(data, offset)
    if data_type == "dint":
        from snap7.util import get_dint

        return get_dint(data, offset)
    if data_type == "real":
        from snap7.util import get_real

        return get_real(data, offset)
    if data_type == "string":
        return _decode_s7_string(data[offset : offset + point["length"]])
    raise ValueError(f"unsupported data type: {data_type}")


@dataclass
class S7NodeReadItem:
    comment: str
    address: str
    ok: bool
    value: str
    error: str = ""


def _format_s7_address(point: dict) -> str:
    db_number = point["db_number"]
    offset = point["offset"]
    data_type = point["data_type"]
    if data_type == "bool":
        return f"DB{db_number}.DBX{offset}.{point['bit']}"
    if data_type == "int":
        return f"DB{db_number}.DBW{offset}"
    if data_type in {"dint", "real"}:
        return f"DB{db_number}.DBD{offset}"
    return f"DB{db_number}.DBB{offset}..{offset + point['length'] - 1}"


def _read_s7_nodes(connection_config: dict, node=None) -> tuple[ConnectionTestResult, list[S7NodeReadItem]]:
    host = (connection_config.get("host") or "").strip()
    if not host:
        return ConnectionTestResult(False, "PLC 主机地址不能为空"), []

    try:
        rack = _coerce_int(connection_config.get("rack"), field="rack", default=0, min_value=0)
        slot = _coerce_int(connection_config.get("slot"), field="slot", default=1, min_value=0)
    except ValueError as exc:
        return ConnectionTestResult(False, str(exc)), []

    nodes = _normalize_s7_nodes(node)
    try:
        import snap7
    except ImportError:
        return (
            ConnectionTestResult(
                False,
                "未安装 python-snap7，请在 backend/requirements.txt 中安装依赖后重试",
            ),
            [],
        )

    client = snap7.client.Client()
    items: list[S7NodeReadItem] = []
    try:
        client.connect(host, rack, slot)
        if not client.get_connected():
            return ConnectionTestResult(False, f"S7 PLC 连接失败: {host} (rack={rack}, slot={slot})"), []

        if not nodes:
            return ConnectionTestResult(True, f"成功连接 S7 PLC {host} (rack={rack}, slot={slot})"), []

        db_blocks: dict[int, bytes] = {}
        for db_number, (start, end) in _s7_db_read_ranges(nodes).items():
            size = max(1, end - start)
            db_blocks[db_number] = client.db_read(db_number, start, size)

        for point in nodes:
            address = _format_s7_address(point)
            try:
                db_number = point["db_number"]
                start, _ = _s7_db_read_ranges(nodes)[db_number]
                point_with_start = {**point, "_read_start": start}
                raw_value = _parse_s7_value(db_blocks[db_number], point_with_start)
                items.append(
                    S7NodeReadItem(
                        comment=point["comment"],
                        address=address,
                        ok=True,
                        value=str(raw_value),
                    )
                )
            except Exception as exc:
                items.append(
                    S7NodeReadItem(
                        comment=point["comment"],
                        address=address,
                        ok=False,
                        value="",
                        error=_describe_exception(exc),
                    )
                )

        all_ok = all(item.ok for item in items)
        return (
            ConnectionTestResult(
                all_ok,
                f"{'成功连接' if all_ok else '连接或读取异常'} S7 PLC {host} (rack={rack}, slot={slot})",
            ),
            items,
        )
    except Exception as exc:
        return ConnectionTestResult(False, f"S7 PLC 连接失败: {_describe_exception(exc)}"), items
    finally:
        try:
            if client.get_connected():
                client.disconnect()
        except Exception:
            pass


def read_s7_nodes(connection_config: dict, node=None) -> tuple[ConnectionTestResult, list[S7NodeReadItem]]:
    """Read configured S7 DB points (connect per call)."""
    return _read_s7_nodes(connection_config, node=node)


def test_s7_connection(connection_config: dict, node=None) -> ConnectionTestResult:
    """Connect to Siemens S7 PLC and optionally read configured DB points."""
    result, items = _read_s7_nodes(connection_config, node=node)
    if not items:
        return result

    lines = []
    failed = False
    for index, item in enumerate(items, start=1):
        if item.ok:
            lines.append(f"{index}. {item.comment} ({item.address}) = {item.value}")
        else:
            failed = True
            lines.append(f"{index}. {item.comment} ({item.address}) = 获取失败 ({item.error})")
    summary = "\n".join(lines)
    prefix = "成功连接" if not failed and result.ok else "连接或读取异常"
    return ConnectionTestResult(
        (not failed) and result.ok,
        f"{prefix} {result.message}，点位读取结果（按配置顺序）：\n{summary}",
    )
