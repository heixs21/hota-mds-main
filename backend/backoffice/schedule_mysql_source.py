"""MySQL 甘特排产数据源：mach.orders ↔ machines，对接产线台账 lineCode。

后续可并行接入 SAP 等上游：在本模块旁新增 provider，输出相同的 ``orders[]`` 结构即可。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.utils import timezone


def fetch_mysql_schedule_orders_by_line_codes(
    connection_config: dict[str, Any],
    line_codes: list[str],
    window_days: int,
) -> dict[str, list[dict]]:
    """按产线编码拉取未完工工单；时间窗口由服务端按「最早未完成开始日 + 跨度」裁剪。

    ``window_days`` 保留供调用方对齐配置；本查询不按日历窗口过滤。
    联结关系：``orders.machine = machines.name``，``machines.lineCode`` = 产线台账编码。
    失败抛出异常，由调用方决定是否回退快照。
    """
    from .display_services import (  # noqa: WPS433 运行时导入避免循环依赖
        _build_schedule_order_display,
        _mysql_query_rows,
    )

    if not connection_config or not line_codes:
        return {}

    codes = [str(c).strip() for c in line_codes if str(c).strip()]
    if not codes:
        return {}

    today = timezone.localdate()

    placeholders = ",".join(["%s"] * len(codes))
    sql = f"""
SELECT
  m.`lineCode` AS line_code,
  o.orderNo AS order_no,
  o.materialNo AS material_no,
  o.materialName AS material_name,
  o.startDate AS start_date,
  o.expectedEndDate AS expected_end_date,
  o.delayedExpectedEndDate AS delayed_expected_end_date,
  o.actualEndDate AS actual_end_date,
  o.quantity AS quantity,
  o.reportedQuantity AS reported_quantity,
  o.status AS status,
  o.isPaused AS is_paused
FROM `orders` o
INNER JOIN `machines` m ON o.machine = m.name
WHERE m.`lineCode` IS NOT NULL
  AND m.`lineCode` IN ({placeholders})
  AND o.actualEndDate IS NULL
ORDER BY m.`lineCode` ASC, o.priority DESC, o.startDate ASC, o.orderNo ASC
"""
    params = tuple(codes)
    rows = _mysql_query_rows(connection_config, sql, params)

    grouped: dict[str, list[dict]] = {c: [] for c in codes}
    for row in rows:
        lc = row.get("line_code")
        if not lc or lc not in grouped:
            continue
        grouped[lc].append(_map_mysql_row_to_schedule_order(row, today, _build_schedule_order_display))

    return grouped


def _map_mysql_row_to_schedule_order(row: dict, today: date, build_display_fn) -> dict:
    start_d = _parse_mysql_date(row.get("start_date"))
    end_d = _parse_mysql_date(row.get("delayed_expected_end_date"))
    if end_d is None:
        end_d = _parse_mysql_date(row.get("expected_end_date"))
    if end_d is None:
        end_d = start_d
    if start_d is None:
        start_d = today

    qty = int(row.get("quantity") or 0)
    reported = int(row.get("reported_quantity") or 0)
    if qty <= 0:
        completion_rate = 0.0
    else:
        completion_rate = round(min(100.0, max(0.0, reported * 100.0 / qty)), 2)

    risk_status = _resolve_risk_status_mysql(row, today, start_d, end_d)

    disp_start = start_d.isoformat()
    disp_end = end_d.isoformat()
    planned_start_iso = _local_date_start_iso(start_d)
    planned_end_iso = _local_date_start_iso(end_d)

    return {
        "orderCode": str(row.get("order_no") or "").strip() or "--",
        "materialCode": str(row.get("material_no") or "").strip() or "-",
        "materialName": str(row.get("material_name") or "").strip(),
        "status": str(row.get("status") or "").strip() or "未开始",
        "riskStatus": risk_status,
        "targetQuantity": qty,
        "producedQuantity": reported,
        "plannedStartAt": planned_start_iso,
        "plannedEndAt": planned_end_iso,
        "displayStartAt": disp_start,
        "displayEndAt": disp_end,
        "completionRate": completion_rate,
        "display": build_display_fn(risk_status, disp_start, disp_end, completion_rate),
    }


def _parse_mysql_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return timezone.localdate(value) if timezone.is_aware(value) else value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _local_date_start_iso(d: date) -> str:
    dt = timezone.make_aware(datetime.combine(d, datetime.min.time()))
    return dt.isoformat()


def _resolve_risk_status_mysql(row: dict, today: date, start_d: date, end_d: date) -> str:
    if row.get("is_paused"):
        return "paused"
    status_text = str(row.get("status") or "")
    if "暂停" in status_text:
        return "paused"

    effective_end = end_d
    if effective_end < today and not _looks_completed_status(status_text):
        return "delayed"

    if effective_end >= today:
        days_left = (effective_end - today).days
        if 0 <= days_left <= 2 and not _looks_completed_status(status_text):
            return "warning"

    return "normal"


def _looks_completed_status(status_text: str) -> bool:
    for hint in ("完成", "完工", "结案", "关闭", "结束"):
        if hint in status_text:
            return True
    return False
