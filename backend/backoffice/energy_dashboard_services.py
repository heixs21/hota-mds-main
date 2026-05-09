"""
能耗数据采集与设备状态监测看板 — 聚合查询 po_day / po_month / platform_equipment。

电量口径（与业务约定一致）：时段用电量优先使用
  SUM( CAST(live_data AS DECIMAL) * CAST(multiplying_power AS DECIMAL) )
累计读数展示列使用 real_data。
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.utils import timezone

from .models import DataSourceConfig, EnergyDashboardSnapshot

logger = logging.getLogger(__name__)

ENERGY_CATEGORY_LABELS = {1: "照明插座", 2: "空调", 3: "动力", 4: "特殊"}
ENERGY_CATEGORY_COLORS = {1: "#22d3ee", 2: "#38bdf8", 3: "#fb923c", 4: "#a78bfa"}

LOOP_TYPE_LABELS = {
    "0": "无",
    "1": "低压进线柜",
    "2": "低压电容补偿柜",
    "3": "低压电能质量治理柜",
    "4": "低压出线柜",
    "5": "低压联络柜",
    "6": "高压进线柜",
    "7": "高压电容补偿柜",
    "8": "高压电能质量治理柜",
    "9": "高压出线柜",
    "10": "高压联络柜",
}

PROTOCOL_LABELS = {
    1: "Modbus-RTU",
    2: "Modbus-TCP",
    3: "DLT645-1997",
    4: "DLT645-2007",
    5: "IEC103",
    6: "IEC104",
}

STALE_MINUTES = 120


def _mysql_rows(cc: dict, sql: str, params=None) -> list[dict]:
    try:
        import MySQLdb  # type: ignore
        import MySQLdb.cursors  # type: ignore
    except ImportError as exc:
        raise RuntimeError("MySQLdb (mysqlclient) 未安装") from exc

    conn = MySQLdb.connect(
        host=(cc.get("host") or "").strip(),
        port=int(cc.get("port") or 3306),
        user=(cc.get("username") or "").strip(),
        passwd=cc.get("password") or "",
        db=(cc.get("database") or "").strip(),
        charset="utf8mb4",
        connect_timeout=12,
        read_timeout=30,
    )
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(sql, params or ())
        return list(cur.fetchall())
    finally:
        conn.close()


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _q_kwh_live(alias: str = "d") -> str:
    return (
        f"COALESCE(CAST(NULLIF(TRIM({alias}.live_data),'') AS DECIMAL(24,10)), 0) * "
        f"COALESCE(CAST(NULLIF(TRIM({alias}.multiplying_power),'') AS DECIMAL(24,10)), 1)"
    )


def _resolve_connection(data_source_ids: list[int]) -> tuple[dict | None, str | None]:
    if not data_source_ids:
        return None, "未配置数据源 ID"
    sources = list(
        DataSourceConfig.objects.filter(pk__in=data_source_ids, is_enabled=True),
    )
    if not sources:
        return None, "数据源未找到或已禁用"
    cc = sources[0].connection_config or {}
    if not (cc.get("host") or "").strip():
        return None, "数据源连接配置不完整"
    return cc, None


_PLATFORM_EQUIPMENT_SQL = """
SELECT CAST(e_id AS CHAR) AS e_id, TRIM(p_e_name) AS p_e_name
FROM platform_equipment
WHERE is_flag = '0' AND del_flag = '0'
ORDER BY p_e_name
LIMIT 5000
"""


def refresh_energy_equipment_catalog_for_data_sources(data_source_ids: list[int]) -> str | None:
    """从能耗库拉取 platform_equipment 写入本地 EnergyEquipmentCatalog；返回错误文案或 None。"""
    ids = _normalized_source_ids(data_source_ids)
    if not ids:
        return "未配置数据源"
    cc, err = _resolve_connection(ids)
    if not cc:
        return err or "连接不可用"
    ds = DataSourceConfig.objects.filter(pk__in=ids, is_enabled=True).first()
    if not ds:
        return "数据源未找到或已禁用"
    try:
        rows = _mysql_rows(cc, _PLATFORM_EQUIPMENT_SQL)
    except Exception as exc:
        return str(exc)

    from .models import EnergyEquipmentCatalog

    EnergyEquipmentCatalog.objects.filter(data_source=ds).delete()
    batch = []
    for r in rows:
        eid = str(r.get("e_id") or "").strip()
        name = str(r.get("p_e_name") or "").strip()
        if not eid:
            continue
        batch.append(
            EnergyEquipmentCatalog(
                data_source=ds,
                equipment_id=eid,
                display_name=name or eid,
            )
        )
    EnergyEquipmentCatalog.objects.bulk_create(batch, batch_size=400)
    return None


def _equipment_where(filters: dict[str, Any], alias: str = "e") -> tuple[str, list[Any]]:
    parts = [f"{alias}.is_flag = '0'", f"{alias}.del_flag = '0'"]
    params: list[Any] = []
    if filters.get("project_id"):
        parts.append(f"{alias}.project_id = %s")
        params.append(filters["project_id"])
    if filters.get("son_project_id"):
        parts.append(f"{alias}.son_project_id = %s")
        params.append(filters["son_project_id"])
    if filters.get("station_id"):
        parts.append(f"{alias}.station_id = %s")
        params.append(filters["station_id"])
    if filters.get("transformer_id"):
        parts.append(f"{alias}.transformer_id = %s")
        params.append(filters["transformer_id"])
    kw = (filters.get("keyword") or "").strip()
    if kw:
        parts.append(f"({alias}.p_e_name LIKE %s OR {alias}.p_e_code LIKE %s)")
        params.extend([f"%{kw}%", f"%{kw}%"])
    eq_ids = filters.get("equipment_ids") or []
    if eq_ids:
        ph = ",".join(["%s"] * len(eq_ids))
        parts.append(f"{alias}.e_id IN ({ph})")
        params.extend(eq_ids)
    return " AND ".join(parts), params


def _normalized_source_ids(data_source_ids: list[int]) -> list[int]:
    out: set[int] = set()
    for x in data_source_ids or []:
        try:
            i = int(x)
        except (TypeError, ValueError):
            continue
        if i > 0:
            out.add(i)
    return sorted(out)


def _energy_dashboard_cache_key(data_source_ids: list[int], filters: dict[str, Any]) -> str:
    """同一数据源 + 筛选维度对应唯一快照（与 refreshScope 无关，完整明细只存一份）。"""
    canonical = {
        "ds": _normalized_source_ids(data_source_ids),
        "f": {
            "project_id": filters.get("project_id"),
            "son_project_id": filters.get("son_project_id"),
            "station_id": filters.get("station_id"),
            "transformer_id": filters.get("transformer_id"),
            "keyword": filters.get("keyword"),
            "equipment_ids": sorted(filters.get("equipment_ids") or []),
            "date_from": filters["date_from"].isoformat(),
            "date_to": filters["date_to"].isoformat(),
        },
    }
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _persist_energy_dashboard_snapshot(
    data_source_ids: list[int],
    filters: dict[str, Any],
    payload: dict[str, Any],
    *,
    refresh_label: str = "full",
) -> None:
    cache_key = _energy_dashboard_cache_key(data_source_ids, filters)
    store = {k: v for k, v in payload.items() if k != "ok"}
    EnergyDashboardSnapshot.objects.update_or_create(
        cache_key=cache_key,
        defaults={
            "data_source_ids": _normalized_source_ids(data_source_ids),
            "refresh_scope": (refresh_label or "full")[:32],
            "filters": store.get("filtersApplied") or {},
            "snapshot_data": store,
        },
    )


def slice_energy_dashboard_for_live(full_data: dict[str, Any]) -> dict[str, Any]:
    """从完整快照中裁剪轻量字段（轮询带宽）。"""
    out = dict(full_data)
    out["hourlySeries"] = []
    out["dayTrend"] = []
    out["monthTrend"] = []
    return out


def load_energy_dashboard_snapshot_row(
    data_source_ids: list[int],
    filters: dict[str, Any],
):
    ck = _energy_dashboard_cache_key(data_source_ids, filters)
    return EnergyDashboardSnapshot.objects.filter(cache_key=ck).first()


def serve_energy_dashboard(
    data_source_ids: list[int],
    body: dict[str, Any],
    *,
    allow_live_fallback: bool = True,
) -> dict[str, Any]:
    """
    优先返回本地 EnergyDashboardSnapshot；轻量请求仍读库中完整快照并裁剪。
    body.forceRefresh / force_refresh 为真时直连外部能耗库并写回快照。
    """
    filters = _parse_filters(body)
    refresh = (body.get("refreshScope") or body.get("refresh_scope") or "full").lower()
    lightweight = refresh in {"live", "light", "partial"}
    force_live = bool(body.get("forceRefresh") or body.get("force_refresh"))

    if force_live:
        return run_energy_dashboard(
            data_source_ids,
            body,
            persist_snapshot=not lightweight,
        )

    row = load_energy_dashboard_snapshot_row(data_source_ids, filters)
    if row and row.snapshot_data:
        data = dict(row.snapshot_data)
        if lightweight:
            data = slice_energy_dashboard_for_live(data)
        gen_at = timezone.localtime(row.updated_at).isoformat()
        data["generatedAt"] = gen_at
        return {
            **data,
            "ok": True,
            "fromCache": True,
            "snapshotUpdatedAt": gen_at,
        }

    if allow_live_fallback:
        return run_energy_dashboard(
            data_source_ids,
            body,
            persist_snapshot=not lightweight,
        )

    return {
        "ok": False,
        "error": "暂无本地缓存，请等待后台同步任务（sync_energy_dashboard_snapshots）",
        "cacheMiss": True,
    }


def _parse_filters(body: dict[str, Any]) -> dict[str, Any]:
    df = body.get("dateFrom") or body.get("date_from")
    dt = body.get("dateTo") or body.get("date_to")
    today = timezone.localdate()
    date_from = today - timedelta(days=6)
    date_to = today
    if df:
        try:
            date_from = datetime.strptime(str(df)[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    if dt:
        try:
            date_to = datetime.strptime(str(dt)[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    raw_eq = body.get("equipmentIds") or body.get("equipment_ids") or []
    equipment_ids = [str(x) for x in raw_eq if x]

    return {
        "project_id": (body.get("projectId") or body.get("project_id") or "").strip() or None,
        "son_project_id": (body.get("sonProjectId") or body.get("son_project_id") or "").strip() or None,
        "station_id": (body.get("stationId") or body.get("station_id") or "").strip() or None,
        "transformer_id": (body.get("transformerId") or body.get("transformer_id") or "").strip() or None,
        "keyword": (body.get("keyword") or "").strip() or None,
        "equipment_ids": equipment_ids,
        "date_from": date_from,
        "date_to": date_to,
    }


def default_energy_sync_body() -> dict[str, Any]:
    """与前端大屏默认筛选一致（近 7 日），供定时任务写入本地快照。"""
    today = timezone.localdate()
    return {
        "dateFrom": (today - timedelta(days=6)).isoformat(),
        "dateTo": today.isoformat(),
        "refreshScope": "full",
    }


def _short_id(uid: str | None) -> str:
    if not uid:
        return "—"
    u = str(uid).strip()
    return u[:8] + "…" if len(u) > 10 else u


def build_filter_options(cc: dict, filters: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    ew, ep = _equipment_where({**filters, "equipment_ids": [], "keyword": None}, "e")

    def distinct(col: str) -> list[dict[str, str]]:
        sql = f"""
        SELECT DISTINCT {col} AS id FROM platform_equipment e
        WHERE {col} IS NOT NULL AND TRIM({col}) != '' AND {ew}
        """
        rows = _mysql_rows(cc, sql, ep)
        out = []
        for r in rows:
            uid = r.get("id")
            if uid:
                s = str(uid)
                out.append({"id": s, "label": _short_id(s)})
        return out

    return {
        "projects": distinct("project_id"),
        "stations": distinct("station_id"),
        "transformers": distinct("transformer_id"),
    }


def _summary_block(cc: dict, filters: dict[str, Any]) -> dict[str, Any]:
    ew, ep = _equipment_where(filters, "e")
    kwh_live = _q_kwh_live("d")

    row = _mysql_rows(
        cc,
        f"""
        SELECT
          COALESCE(SUM({kwh_live}), 0) AS today_kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) = CURDATE()
          AND {ew}
        """,
        ep,
    )
    today_kwh = _dec(row[0]["today_kwh"]) if row else Decimal("0")

    row_m = _mysql_rows(
        cc,
        f"""
        SELECT COALESCE(SUM({_q_kwh_live('m')}), 0) AS month_kwh
        FROM po_month m
        INNER JOIN platform_equipment e ON m.equipment_ids = e.e_id
        WHERE m.types = 1 AND m.is_flag = '0' AND m.del_flag = '0'
          AND YEAR(m.create_time) = YEAR(CURDATE()) AND MONTH(m.create_time) = MONTH(CURDATE())
          AND {ew}
        """,
        ep,
    )
    month_kwh = _dec(row_m[0]["month_kwh"]) if row_m else Decimal("0")

    cnt_row = _mysql_rows(
        cc,
        f"""
        SELECT
          SUM(CASE WHEN e.p_status = 0 THEN 1 ELSE 0 END) AS running_cnt,
          SUM(CASE WHEN e.p_status = 1 THEN 1 ELSE 0 END) AS abnormal_cnt,
          COUNT(*) AS total_cnt
        FROM platform_equipment e
        WHERE {ew}
        """,
        ep,
    )
    running = int(cnt_row[0]["running_cnt"] or 0) if cnt_row else 0
    abnormal = int(cnt_row[0]["abnormal_cnt"] or 0) if cnt_row else 0

    cat_rows = _mysql_rows(
        cc,
        f"""
        SELECT d.energy_consumption AS cat,
               COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) = CURDATE()
          AND {ew}
        GROUP BY d.energy_consumption
        """,
        ep,
    )
    cat_map: dict[int, Decimal] = {}
    for r in cat_rows:
        try:
            k = int(r.get("cat") or 0)
        except (TypeError, ValueError):
            k = 0
        cat_map[k] = _dec(r.get("kwh"))

    category_mini = []
    for cid in (1, 2, 3, 4):
        val = cat_map.get(cid, Decimal("0"))
        pct = int(val / today_kwh * 100) if today_kwh > 0 else 0
        category_mini.append(
            {
                "id": cid,
                "label": ENERGY_CATEGORY_LABELS.get(cid, "其他"),
                "color": ENERGY_CATEGORY_COLORS.get(cid, "#94a3b8"),
                "kwh": str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "percent": pct,
            }
        )

    y_row = _mysql_rows(
        cc,
        f"""
        SELECT COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
          AND TIME(d.create_time) <= TIME(NOW())
          AND {ew}
        """,
        ep,
    )
    yesterday_window = _dec(y_row[0]["kwh"]) if y_row else Decimal("0")

    t_row = _mysql_rows(
        cc,
        f"""
        SELECT COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) = CURDATE()
          AND TIME(d.create_time) <= TIME(NOW())
          AND {ew}
        """,
        ep,
    )
    today_window = _dec(t_row[0]["kwh"]) if t_row else Decimal("0")

    if yesterday_window > 0:
        yoy = float(((today_window - yesterday_window) / yesterday_window * 100).quantize(Decimal("0.1")))
    else:
        yoy = 0.0 if today_window == 0 else 100.0

    return {
        "todayKwh": str(today_kwh.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "monthKwh": str(month_kwh.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "runningDeviceCount": running,
        "abnormalDeviceCount": abnormal,
        "categoryMiniBars": category_mini,
        "yesterdaySameWindowKwh": str(yesterday_window.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "todaySameWindowKwh": str(today_window.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "yoyPercent": yoy,
        "unit": "kWh",
    }


def _equipment_tree(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    ew, ep = _equipment_where(filters, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT e.e_id, e.p_e_name, e.p_e_code, e.project_id, e.son_project_id,
               e.station_id, e.transformer_id, e.p_serial_number, e.p_baud_rate,
               e.p_status, e.is_flag, e.p_protocol_type, e.p_salve_id, e.modify_time,
               e.p_id_pid, e.p_sorts
        FROM platform_equipment e
        WHERE {ew}
        ORDER BY e.project_id, e.station_id, e.transformer_id, e.p_sorts, e.p_e_code
        """,
        ep,
    )

    projects: dict[str, dict] = {}

    def nid(kind: str, uid: str | None) -> str:
        return f"{kind}:{uid or 'none'}"

    for r in rows:
        pid = str(r.get("project_id") or "") or "unknown"
        sid = str(r.get("station_id") or "") or "none"
        tid = str(r.get("transformer_id") or "") or "none"

        if pid not in projects:
            projects[pid] = {
                "id": nid("project", pid),
                "type": "project",
                "label": f"项目 {_short_id(pid)}",
                "rawId": pid,
                "children": {},
            }
        pr = projects[pid]
        stations: dict = pr["children"]
        if sid not in stations:
            stations[sid] = {
                "id": nid("station", f"{pid}:{sid}"),
                "type": "station",
                "label": f"站点 {_short_id(sid)}",
                "rawId": sid,
                "children": {},
            }
        st = stations[sid]["children"]
        if tid not in st:
            st[tid] = {
                "id": nid("transformer", f"{pid}:{sid}:{tid}"),
                "type": "transformer",
                "label": f"变压器 {_short_id(tid)}",
                "rawId": tid,
                "children": [],
            }
        tr = st[tid]
        st_val = r.get("p_status")
        active = str(r.get("is_flag") or "0") == "0"
        if not active:
            comm = "disabled"
        elif st_val == 1:
            comm = "abnormal"
        else:
            comm = "normal"

        proto = r.get("p_protocol_type")
        proto_label = ""
        if proto is not None:
            try:
                proto_label = PROTOCOL_LABELS.get(int(proto), str(proto))
            except (TypeError, ValueError):
                proto_label = str(proto)
        tr["children"].append(
            {
                "id": str(r["e_id"]),
                "type": "equipment",
                "label": r.get("p_e_name") or r.get("p_e_code") or "设备",
                "code": r.get("p_e_code") or "",
                "serial": r.get("p_serial_number") or "",
                "baudRate": r.get("p_baud_rate"),
                "commStatus": comm,
                "tooltip": {
                    "protocol": proto_label,
                    "address": r.get("p_salve_id") or "",
                    "lastModify": str(r.get("modify_time") or ""),
                },
            }
        )

    def nest_map_to_list(m: dict) -> list:
        out = []
        for node in m.values():
            ch = node.get("children")
            if isinstance(ch, dict):
                node["children"] = nest_map_to_list(ch)
            elif isinstance(ch, list):
                pass
            out.append(node)
        return out

    return nest_map_to_list(projects)


def _table_rows(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    """主设备摘要（进线柜）或选中设备的明细。"""
    sel = filters.get("equipment_ids") or []
    ew_base, ep_base = _equipment_where(filters, "e")
    kwh_live = _q_kwh_live("d")

    if sel:
        eq_filter = {**filters, "equipment_ids": sel}
        ew, ep = _equipment_where(eq_filter, "e")
        eq_rows = _mysql_rows(
            cc,
            f"SELECT e.e_id FROM platform_equipment e WHERE {ew}",
            ep,
        )
    else:
        # loop_type 在 po_day 上，不在 platform_equipment；用当日日表关联筛选「进线柜」类设备
        eq_rows = _mysql_rows(
            cc,
            f"""
            SELECT DISTINCT e.e_id
            FROM platform_equipment e
            INNER JOIN po_day d ON d.equipment_ids = e.e_id
              AND d.types = 1
              AND d.loop_type IN ('1','6')
              AND d.is_flag = '0'
              AND d.del_flag = '0'
              AND DATE(d.create_time) = CURDATE()
            WHERE {ew_base}
            """,
            ep_base,
        )
    eids = [str(x["e_id"]) for x in eq_rows]
    if not eids:
        return []

    out = []
    for eid in eids[:500]:
        meta = _mysql_rows(
            cc,
            """
            SELECT p_e_name, p_e_code, p_status, is_flag FROM platform_equipment e WHERE e.e_id = %s
            """,
            [eid],
        )
        name = meta[0].get("p_e_name") if meta else ""
        code = meta[0].get("p_e_code") if meta else ""
        pst = meta[0].get("p_status") if meta else None
        inactive = str(meta[0].get("is_flag")) == "1" if meta else False

        latest = _mysql_rows(
            cc,
            """
            SELECT real_data, live_data, multiplying_power, loop_type, energy_consumption,
                   create_time, modify_time
            FROM po_day
            WHERE types = 1 AND equipment_ids = %s
            ORDER BY create_time DESC LIMIT 1
            """,
            [eid],
        )

        last_hour = _mysql_rows(
            cc,
            f"""
            SELECT COALESCE(SUM({kwh_live}), 0) AS kwh
            FROM po_day d
            WHERE d.types = 1 AND d.equipment_ids = %s
              AND d.create_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """,
            [eid],
        )
        today_sum = _mysql_rows(
            cc,
            f"""
            SELECT COALESCE(SUM({kwh_live}), 0) AS kwh
            FROM po_day d
            WHERE d.types = 1 AND d.equipment_ids = %s
              AND DATE(d.create_time) = CURDATE()
            """,
            [eid],
        )

        lr = latest[0] if latest else {}
        lt = lr.get("create_time") or lr.get("modify_time")
        stale = False
        if lt and isinstance(lt, datetime):
            now_naive = timezone.now().replace(tzinfo=None)
            lt_naive = lt.replace(tzinfo=None) if getattr(lt, "tzinfo", None) else lt
            stale = (now_naive - lt_naive).total_seconds() > STALE_MINUTES * 60

        loop_raw = str(lr.get("loop_type") or "")
        ec = lr.get("energy_consumption")
        ec_label = "—"
        if ec is not None:
            try:
                ec_label = ENERGY_CATEGORY_LABELS.get(int(ec), "—")
            except (TypeError, ValueError):
                ec_label = "—"
        warn_row = (pst == 1) or stale

        out.append(
            {
                "equipmentId": eid,
                "equipmentName": name or code or eid,
                "equipmentCode": code or "",
                "commNormal": not inactive and pst != 1,
                "reading": str(lr.get("real_data") or "—"),
                "lastHourKwh": str(_dec(last_hour[0]["kwh"]).quantize(Decimal("0.01"))) if last_hour else "0.00",
                "todayKwh": str(_dec(today_sum[0]["kwh"]).quantize(Decimal("0.01"))) if today_sum else "0.00",
                "loopType": LOOP_TYPE_LABELS.get(loop_raw, loop_raw or "—"),
                "energyCategory": ec_label,
                "multiplyingPower": str(lr.get("multiplying_power") or ""),
                "lastCommTime": str(lr.get("create_time") or lr.get("modify_time") or ""),
                "rowAlert": warn_row,
                "inactive": inactive,
            }
        )
    return out


def _hourly_series(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    sel = filters.get("equipment_ids") or []
    kwh_live = _q_kwh_live("d")
    if sel:
        ph = ",".join(["%s"] * len(sel))
        cond = f"d.equipment_ids IN ({ph})"
        params = list(sel)
    else:
        ew, ep = _equipment_where(filters, "e")
        cond = f"""d.equipment_ids IN (
            SELECT DISTINCT e.e_id
            FROM platform_equipment e
            INNER JOIN po_day d2 ON d2.equipment_ids = e.e_id
              AND d2.types = 1
              AND d2.loop_type IN ('1','6')
              AND d2.is_flag = '0'
              AND d2.del_flag = '0'
              AND DATE(d2.create_time) = CURDATE()
            WHERE {ew}
        )"""
        params = ep

    rows = _mysql_rows(
        cc,
        f"""
        SELECT HOUR(d.create_time) AS hr, COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) = CURDATE()
          AND {cond}
        GROUP BY HOUR(d.create_time)
        ORDER BY hr
        """,
        params,
    )
    by_h = {int(r["hr"]): _dec(r["kwh"]) for r in rows if r.get("hr") is not None}
    series = []
    for h in range(24):
        v = by_h.get(h, Decimal("0"))
        series.append(
            {"hour": h, "kwh": str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))},
        )
    return series


def _day_trend(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    df = filters["date_from"]
    dt = filters["date_to"]
    kwh_live = _q_kwh_live("d")
    ew, ep = _equipment_where(filters, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT DATE(d.create_time) AS d, COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) BETWEEN %s AND %s
          AND {ew}
        GROUP BY DATE(d.create_time)
        ORDER BY d
        """,
        [df, dt] + ep,
    )
    out = []
    for r in rows:
        ds = r["d"]
        if hasattr(ds, "isoformat"):
            ds_s = ds.isoformat()
        else:
            ds_s = str(ds)
        out.append(
            {
                "date": ds_s,
                "kwh": str(_dec(r["kwh"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            }
        )
    return out


def _month_trend(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    ew, ep = _equipment_where(filters, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT
          DATE_FORMAT(m.create_time, '%%Y-%%m') AS ym,
          COALESCE(SUM({_q_kwh_live('m')}), 0) AS kwh
        FROM po_month m
        INNER JOIN platform_equipment e ON m.equipment_ids = e.e_id
        WHERE m.types = 1 AND m.is_flag = '0' AND m.del_flag = '0'
          AND m.create_time >= DATE_SUB(CURDATE(), INTERVAL 14 MONTH)
          AND {ew}
        GROUP BY DATE_FORMAT(m.create_time, '%%Y-%%m')
        ORDER BY ym
        """,
        ep,
    )
    return [
        {
            "month": r["ym"],
            "kwh": str(_dec(r["kwh"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        }
        for r in rows
    ]


def _classification_pie(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    df = filters["date_from"]
    dt = filters["date_to"]
    kwh_live = _q_kwh_live("d")
    ew, ep = _equipment_where(filters, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT d.energy_consumption AS cat, COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) BETWEEN %s AND %s
          AND {ew}
        GROUP BY d.energy_consumption
        """,
        [df, dt] + ep,
    )
    total = sum(_dec(r["kwh"]) for r in rows)
    pie = []
    for r in rows:
        try:
            cat = int(r.get("cat") or 0)
        except (TypeError, ValueError):
            cat = 0
        val = _dec(r["kwh"])
        pct = float((val / total * 100).quantize(Decimal("0.1"))) if total > 0 else 0.0
        pie.append(
            {
                "id": cat,
                "label": ENERGY_CATEGORY_LABELS.get(cat, "其他"),
                "color": ENERGY_CATEGORY_COLORS.get(cat, "#64748b"),
                "kwh": str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "percent": pct,
            }
        )
    return pie


def _loop_ranking(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    df = filters["date_from"]
    dt = filters["date_to"]
    kwh_live = _q_kwh_live("d")
    ew, ep = _equipment_where(filters, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT d.loop_type AS lp, COALESCE(SUM({kwh_live}), 0) AS kwh
        FROM po_day d
        INNER JOIN platform_equipment e ON d.equipment_ids = e.e_id
        WHERE d.types = 1 AND d.is_flag = '0' AND d.del_flag = '0'
          AND DATE(d.create_time) BETWEEN %s AND %s
          AND {ew}
        GROUP BY d.loop_type
        ORDER BY kwh DESC
        LIMIT 5
        """,
        [df, dt] + ep,
    )
    out = []
    for r in rows:
        lp = str(r.get("lp") or "")
        out.append(
            {
                "loopType": LOOP_TYPE_LABELS.get(lp, lp or "—"),
                "kwh": str(_dec(r["kwh"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            }
        )
    return out


def _alarms(cc: dict, filters: dict[str, Any]) -> list[dict[str, Any]]:
    ew, ep = _equipment_where({**filters, "equipment_ids": []}, "e")
    rows = _mysql_rows(
        cc,
        f"""
        SELECT e.e_id, e.p_e_name, e.p_e_code, e.modify_time, e.transformer_id
        FROM platform_equipment e
        WHERE {ew} AND e.p_status = 1
        ORDER BY e.modify_time DESC
        LIMIT 50
        """,
        ep,
    )
    alarms = []
    for r in rows:
        alarms.append(
            {
                "equipmentId": str(r["e_id"]),
                "equipmentName": r.get("p_e_name") or r.get("p_e_code"),
                "equipmentCode": r.get("p_e_code") or "",
                "lastCommTime": str(r.get("modify_time") or ""),
                "transformerLabel": _short_id(str(r.get("transformer_id"))),
            }
        )
    return alarms


def run_energy_dashboard(
    data_source_ids: list[int],
    body: dict[str, Any],
    *,
    persist_snapshot: bool = False,
) -> dict[str, Any]:
    cc, err = _resolve_connection(data_source_ids)
    if not cc:
        return {"ok": False, "error": err or "连接不可用"}

    filters = _parse_filters(body)
    refresh = (body.get("refreshScope") or body.get("refresh_scope") or "full").lower()
    lightweight = refresh in {"live", "light", "partial"}

    try:
        summary = _summary_block(cc, filters)
        filter_options = build_filter_options(cc, filters)
        tree = _equipment_tree(cc, filters)
        table = _table_rows(cc, filters)
        alarms = _alarms(cc, filters)

        payload: dict[str, Any] = {
            "ok": True,
            "pageTitle": "能耗数据采集与设备状态监测看板",
            "summary": summary,
            "filterOptions": filter_options,
            "equipmentTree": tree,
            "table": table,
            "alarms": alarms,
            "filtersApplied": {
                "projectId": filters.get("project_id"),
                "stationId": filters.get("station_id"),
                "transformerId": filters.get("transformer_id"),
                "dateFrom": filters["date_from"].isoformat(),
                "dateTo": filters["date_to"].isoformat(),
                "equipmentIds": filters.get("equipment_ids") or [],
            },
            "generatedAt": timezone.localtime().isoformat(),
        }

        payload["classificationPie"] = _classification_pie(cc, filters)
        payload["loopRanking"] = _loop_ranking(cc, filters)

        if not lightweight:
            payload["hourlySeries"] = _hourly_series(cc, filters)
            payload["dayTrend"] = _day_trend(cc, filters)
            payload["monthTrend"] = _month_trend(cc, filters)
        else:
            payload["hourlySeries"] = []
            payload["dayTrend"] = []
            payload["monthTrend"] = []

        if persist_snapshot and not lightweight:
            try:
                _persist_energy_dashboard_snapshot(
                    data_source_ids,
                    filters,
                    payload,
                    refresh_label=refresh,
                )
            except Exception:
                logger.warning("energy dashboard snapshot persist failed", exc_info=True)

        return payload
    except Exception as exc:
        logger.exception("energy dashboard failed")
        return {"ok": False, "error": str(exc)}
