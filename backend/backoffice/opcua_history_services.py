"""OPC UA 读点历史落库（无 mock；由 read_opcua_nodes 在带上下文时写入）。"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from .connection_test_services import OpcUaReadResult

logger = logging.getLogger(__name__)

PAYLOAD_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class OpcUaHistoryWriteContext:
    """写入 OpcUaHistorySample 时由调用方提供的上下文。"""

    data_source_id: int
    trigger: str
    device_id: int | None = None
    area_id: int | None = None
    caller_detail: str = ""


def persist_opcua_read(result: "OpcUaReadResult", history: OpcUaHistoryWriteContext, duration_ms: int) -> None:
    """将一次 OPC 读结果写入历史表；失败仅打日志。"""
    from django.conf import settings

    if getattr(settings, "OPCUA_HISTORY_DISABLED", False):
        return

    from .models import OpcUaHistorySample

    items_json = [
        {
            "comment": it.comment,
            "nodeId": it.node_id,
            "ok": it.ok,
            "value": it.value,
            "error": it.error,
        }
        for it in result.items
    ]
    payload = {
        "schemaVersion": PAYLOAD_SCHEMA_VERSION,
        "callerDetail": history.caller_detail or "",
        "opcuaRead": {
            "ok": result.ok,
            "offline": result.offline,
            "message": result.message,
            "endpoint": result.endpoint,
            "sourceInfo": result.source_info,
            "items": items_json,
        },
    }
    raw = json.dumps(payload, ensure_ascii=False)
    payload_bytes = len(raw.encode("utf-8"))
    item_count = len(result.items)
    failure_summary = ""
    if result.offline:
        failure_summary = (result.message or "offline")[:512]
    elif not result.ok and result.items:
        for it in result.items:
            if not it.ok and it.error:
                failure_summary = it.error[:512]
                break
        if not failure_summary:
            failure_summary = (result.message or "read failed")[:512]
    elif not result.ok:
        failure_summary = (result.message or "read failed")[:512]

    OpcUaHistorySample.objects.create(
        data_source_id=history.data_source_id,
        device_id=history.device_id,
        area_id=history.area_id,
        fetched_at=timezone.now(),
        payload=payload,
        payload_version=PAYLOAD_SCHEMA_VERSION,
        read_ok=bool(result.ok),
        offline=bool(result.offline),
        item_count=item_count or None,
        failure_summary=failure_summary,
        duration_ms=max(0, int(duration_ms)) if duration_ms is not None else None,
        payload_bytes=payload_bytes,
        trigger=history.trigger[:64],
    )
