from __future__ import annotations

import concurrent.futures
import logging
import re
import threading
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import close_old_connections, transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .models import (
    Area,
    DataSourceConfig,
    DataSourceHealthSnapshot,
    Device,
    DeviceStatusSnapshot,
    DisplayContentConfig,
    EnergySnapshot,
    ProductionLine,
    ProductionSnapshot,
    RuntimeParameterConfig,
    ScheduleSnapshot,
    ScreenConfig,
    ScreenPageBinding,
)
from .connection_test_services import read_opcua_nodes, test_database_connection, test_opcua_connection
from .serializers import (
    DataSourceHealthSnapshotSerializer,
    DeviceStatusSnapshotSerializer,
    EnergySnapshotSerializer,
    ProductionSnapshotSerializer,
    ScheduleSnapshotSerializer,
)


logger = logging.getLogger(__name__)
SNAPSHOT_KEY_DEFAULT = "default"
DEVICE_STATUS_REFRESH_INTERVAL_SECONDS = 30
_DEVICE_STATUS_REFRESH_LOCK = threading.Lock()
_DEVICE_STATUS_REFRESH_RUNNING = False
_DEVICE_STATUS_REFRESH_LAST_TRIGGERED_AT = None

SCREEN_SOURCE_KEYS = {
    "left": ["device", "production", "energy"],
    "right": ["schedule"],
}
DEFAULT_SCREEN_CONFIGS = {
    "left": {
        "screenKey": "left",
        "title": "左屏综合运行展示",
        "subtitle": "外部参观综合运行视图",
        "rotationIntervalSeconds": 60,
        "pageKeys": ["overview", "operations", "energy", "realtime"],
        "moduleSettings": {
            "deviceOverview": True,
            "productionOverview": True,
            "productionTrend": True,
            "energyOverview": True,
            "repairPlaceholder": True,
            "deviceRealtimeMonitor": True,
        },
        "themeSettings": {},
        "isActive": True,
    },
    "right": {
        "screenKey": "right",
        "title": "右屏生产动态展示",
        "subtitle": "外部参观生产动态视图",
        "rotationIntervalSeconds": 60,
        "pageKeys": ["schedule", "risk", "simulation"],
        "moduleSettings": {
            "schedule": True,
            "delayLegend": True,
            "simulationPlaceholder": True,
        },
        "themeSettings": {},
        "isActive": True,
    },
}
DEFAULT_DISPLAY_CONTENT = {
    "configKey": "default",
    "companyName": "和泰智造",
    "welcomeMessage": "欢迎莅临参观指导",
    "logoUrl": "",
    "promoImageUrls": [],
    "isActive": True,
}
DEFAULT_RUNTIME_PARAMETERS = {
    "configKey": "default",
    "singleDayEffectiveWorkHours": "16.00",
    "defaultStandardCapacityPerHour": "120.00",
    "delayWarningBufferHours": "2.00",
    "ganttWindowDays": 30,
    "autoScrollEnabled": True,
    "autoScrollRowsThreshold": 10,
    "recentCapacityWindowHours": 2,
    "productionTrendWindowHours": 8,
    "notes": "",
    "isActive": True,
}
SOURCE_CATALOG = {
    "device": "设备数据",
    "production": "产量数据",
    "schedule": "排产数据",
    "energy": "能耗数据",
}
DEVICE_STATUS_DISPLAY = {
    Device.STATUS_RUNNING: {"label": "运行", "accent": "green"},
    Device.STATUS_STOPPED: {"label": "停机", "accent": "amber"},
    Device.STATUS_ALARM: {"label": "报警", "accent": "red"},
    Device.STATUS_OFFLINE: {"label": "离线", "accent": "muted"},
}
RISK_STATUS_DISPLAY = {
    "normal": {"label": "正常", "color": "#1f8b4c", "accent": "green"},
    "warning": {"label": "风险", "color": "#d28716", "accent": "amber"},
    "delayed": {"label": "延期", "color": "#c0362c", "accent": "red"},
    "paused": {"label": "暂停", "color": "#6b7280", "accent": "muted"},
}


def get_screen_payload(screen_key: str, area_code: str | None = None) -> dict:
    ensure_mock_snapshots()
    _refresh_device_runtime_statuses_if_needed()
    area = _resolve_area(area_code)

    device_snapshot = DeviceStatusSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)
    production_snapshot = ProductionSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)
    schedule_snapshot = ScheduleSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)
    energy_snapshot = EnergySnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)

    screen_config = _get_screen_config(screen_key, area)
    display_content = _get_display_content()
    runtime_parameters = _get_runtime_parameters()
    health_statuses = _get_health_statuses()
    relevant_statuses = [item for item in health_statuses if item["sourceKey"] in SCREEN_SOURCE_KEYS[screen_key]]
    last_success_at = _max_iso_datetime(
        [
            device_snapshot.last_success_at,
            production_snapshot.last_success_at,
            schedule_snapshot.last_success_at,
            energy_snapshot.last_success_at,
        ]
    )

    payload = {
        "screen": screen_config,
        "content": {
            "welcome": {
                "companyName": display_content["companyName"],
                "welcomeMessage": display_content["welcomeMessage"],
                "logoUrl": display_content["logoUrl"],
                "promoImageUrls": display_content["promoImageUrls"],
                "currentTime": timezone.localtime().isoformat(),
            },
        },
        "meta": {
            "areaCode": area.code,
            "areaName": area.name,
            "lastSuccessfulAt": last_success_at,
            "usingFallback": any(item["fallbackInUse"] for item in relevant_statuses),
            "dataSources": relevant_statuses,
            "display": _build_payload_meta_display(last_success_at),
        },
    }

    if screen_key == "left":
        area_device_overview = _build_area_device_overview(area)
        filtered_line_summaries = _filter_line_summaries_by_area(production_snapshot.line_summaries, area)
        total_target_quantity = sum(int(item.get("targetQuantity") or 0) for item in filtered_line_summaries)
        total_produced_quantity = sum(int(item.get("producedQuantity") or 0) for item in filtered_line_summaries)
        area_completion_rate = _percentage(total_produced_quantity, total_target_quantity)
        filtered_area_summaries = _filter_area_energy_summaries_by_area(energy_snapshot.area_summaries, area)

        device_overview = {
            "totalCount": area_device_overview["total_count"],
            "runningCount": area_device_overview["running_count"],
            "abnormalCount": area_device_overview["abnormal_count"],
            "statusBreakdown": area_device_overview["status_breakdown"],
            "generatedAt": timezone.localtime().isoformat(),
            "sourceUpdatedAt": device_snapshot.source_updated_at.isoformat() if device_snapshot.source_updated_at else None,
            "lastSuccessAt": device_snapshot.last_success_at.isoformat() if device_snapshot.last_success_at else None,
        }
        device_overview["statusItems"] = _build_device_status_items(area_device_overview["status_breakdown"])
        device_overview["display"] = _build_device_overview_display(
            area_device_overview["total_count"],
            area_device_overview["running_count"],
            area_device_overview["abnormal_count"],
            device_snapshot.source_updated_at,
        )
        payload["content"].update(
            {
                "deviceOverview": device_overview,
                "productionOverview": {
                    "totalTargetQuantity": total_target_quantity,
                    "totalProducedQuantity": total_produced_quantity,
                    "overallCompletionRate": str(area_completion_rate),
                    "lineSummaries": filtered_line_summaries,
                    "display": _build_production_overview_display(
                        total_target_quantity,
                        total_produced_quantity,
                        area_completion_rate,
                    ),
                },
                "productionTrend": production_snapshot.trend_points,
                "energyOverview": {
                    "totalConsumption": _sum_energy_consumption(filtered_area_summaries),
                    "unit": energy_snapshot.unit,
                    "areaSummaries": filtered_area_summaries,
                    "display": _build_energy_overview_display(
                        _sum_energy_consumption(filtered_area_summaries),
                        energy_snapshot.unit,
                    ),
                },
                "repairPlaceholder": {
                    "title": "报修模块待一期后段接入",
                    "description": "当前阶段仅保留展示位置，不作为一期前段阻塞项。",
                    "enabled": bool(screen_config["moduleSettings"].get("repairPlaceholder", True)),
                },
            }
        )
    else:
        filtered_line_schedules = _filter_line_schedules_by_area(schedule_snapshot.line_schedules, area)
        risk_counts = _build_risk_counts(filtered_line_schedules)
        payload["content"].update(
            {
                "schedule": {
                    "windowDays": runtime_parameters["ganttWindowDays"],
                    "autoScrollEnabled": runtime_parameters["autoScrollEnabled"],
                    "autoScrollRowsThreshold": runtime_parameters["autoScrollRowsThreshold"],
                    "lineSchedules": filtered_line_schedules,
                    "display": _build_schedule_display(runtime_parameters["ganttWindowDays"]),
                    "riskSummary": {
                        **schedule_snapshot.risk_summary,
                        "counts": risk_counts,
                        "items": _build_risk_summary_items(risk_counts),
                    },
                },
                "delayLegend": schedule_snapshot.legend_items,
                "simulationPlaceholder": {
                    "title": "3D 仿真待一期后段接入",
                    "description": "当前阶段只保留预留区，优先级低于一期前段核心展示链路。",
                    "enabled": bool(screen_config["moduleSettings"].get("simulationPlaceholder", True)),
                },
            }
        )

    # 无论左右屏，只要 realtime 页面在轮播列表中就构建实时监控数据
    if "realtime" in screen_config.get("pageKeys", []):
        payload["content"]["deviceRealtimeMonitor"] = _build_device_realtime_monitor(
            area,
            data_source_ids=_page_binding_data_source_ids(screen_config, "realtime"),
        )

    # 能耗数据页面
    if "energy" in screen_config.get("pageKeys", []):
        payload["content"]["energyData"] = _build_energy_data_page(
            data_source_ids=_page_binding_data_source_ids(screen_config, "energy"),
        )

    return payload


def ensure_mock_snapshots() -> None:
    has_all_snapshots = (
        DeviceStatusSnapshot.objects.filter(snapshot_key=SNAPSHOT_KEY_DEFAULT).exists()
        and ProductionSnapshot.objects.filter(snapshot_key=SNAPSHOT_KEY_DEFAULT).exists()
        and ScheduleSnapshot.objects.filter(snapshot_key=SNAPSHOT_KEY_DEFAULT).exists()
        and EnergySnapshot.objects.filter(snapshot_key=SNAPSHOT_KEY_DEFAULT).exists()
    )
    if has_all_snapshots:
        return
    load_mock_display_data()


@transaction.atomic
def load_mock_display_data(*, simulate_failure: bool = False) -> dict:
    current_time = timezone.now()

    if simulate_failure:
        for source_key, display_name in SOURCE_CATALOG.items():
            existing = DataSourceHealthSnapshot.objects.filter(source_key=source_key).first()
            DataSourceHealthSnapshot.objects.update_or_create(
                source_key=source_key,
                defaults={
                    "display_name": display_name,
                    "status": DataSourceHealthSnapshot.STATUS_FAILED,
                    "last_success_at": existing.last_success_at if existing else None,
                    "last_attempt_at": current_time,
                    "is_stale": True,
                    "fallback_in_use": bool(existing and existing.last_success_at),
                    "error_message": "mock refresh failed; serving last successful snapshot",
                    "details": {"mode": "mock", "reason": "simulated_failure"},
                },
            )
        return {
            "mode": "failure",
            "healthCount": DataSourceHealthSnapshot.objects.count(),
        }

    runtime_parameters = _get_runtime_parameters()
    source_updated_at = current_time - timedelta(minutes=2)
    device_snapshot = _build_device_snapshot(current_time, source_updated_at)
    production_snapshot = _build_production_snapshot(current_time, source_updated_at, runtime_parameters)
    schedule_snapshot = _build_schedule_snapshot(current_time, source_updated_at, runtime_parameters, production_snapshot)
    energy_snapshot = _build_energy_snapshot(current_time, source_updated_at)

    DeviceStatusSnapshot.objects.update_or_create(
        snapshot_key=SNAPSHOT_KEY_DEFAULT,
        defaults=device_snapshot,
    )
    ProductionSnapshot.objects.update_or_create(
        snapshot_key=SNAPSHOT_KEY_DEFAULT,
        defaults=production_snapshot,
    )
    ScheduleSnapshot.objects.update_or_create(
        snapshot_key=SNAPSHOT_KEY_DEFAULT,
        defaults=schedule_snapshot,
    )
    EnergySnapshot.objects.update_or_create(
        snapshot_key=SNAPSHOT_KEY_DEFAULT,
        defaults=energy_snapshot,
    )

    for source_key, display_name in SOURCE_CATALOG.items():
        DataSourceHealthSnapshot.objects.update_or_create(
            source_key=source_key,
            defaults={
                "display_name": display_name,
                "status": DataSourceHealthSnapshot.STATUS_HEALTHY,
                "last_success_at": current_time,
                "last_attempt_at": current_time,
                "is_stale": False,
                "fallback_in_use": False,
                "error_message": "",
                "details": {"mode": "mock"},
            },
        )

    return {
        "mode": "success",
        "generatedAt": current_time.isoformat(),
        "snapshots": {
            "device": DeviceStatusSnapshotSerializer(DeviceStatusSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)).data,
            "production": ProductionSnapshotSerializer(
                ProductionSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)
            ).data,
            "schedule": ScheduleSnapshotSerializer(ScheduleSnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)).data,
            "energy": EnergySnapshotSerializer(EnergySnapshot.objects.get(snapshot_key=SNAPSHOT_KEY_DEFAULT)).data,
        },
        "health": _get_health_statuses(),
    }


def _build_device_snapshot(current_time, source_updated_at) -> dict:
    devices = list(Device.objects.filter(is_active=True).order_by("code"))
    status_breakdown = {
        Device.STATUS_RUNNING: 0,
        Device.STATUS_STOPPED: 0,
        Device.STATUS_ALARM: 0,
        Device.STATUS_OFFLINE: 0,
    }

    if devices:
        for device in devices:
            status_breakdown[device.default_status] = status_breakdown.get(device.default_status, 0) + 1
        total_count = len(devices)
    else:
        status_breakdown = {
            Device.STATUS_RUNNING: 4,
            Device.STATUS_STOPPED: 1,
            Device.STATUS_ALARM: 1,
            Device.STATUS_OFFLINE: 0,
        }
        total_count = 6

    running_count = status_breakdown.get(Device.STATUS_RUNNING, 0)
    abnormal_count = max(total_count - running_count, 0)
    return {
        "total_count": total_count,
        "running_count": running_count,
        "abnormal_count": abnormal_count,
        "status_breakdown": status_breakdown,
        "generated_at": current_time,
        "source_updated_at": source_updated_at,
        "last_success_at": current_time,
    }


def _build_production_snapshot(current_time, source_updated_at, runtime_parameters: dict) -> dict:
    lines = list(ProductionLine.objects.filter(is_active=True).select_related("area").order_by("code"))
    if not lines:
        lines = [
            _FallbackLine("L01", "装配一线", "总装区"),
            _FallbackLine("L02", "装配二线", "总装区"),
            _FallbackLine("L03", "包装线", "包装区"),
        ]

    minimum_lines = max(len(lines), 8)

    line_summaries = []
    total_target = 0
    total_produced = 0
    for index in range(minimum_lines):
        source_line = lines[index % len(lines)]
        line_number = index + 1
        line_code = source_line.code if index < len(lines) else f"MOCK-L{line_number:02d}"
        line_name = source_line.name if index < len(lines) else f"{getattr(source_line, 'area_name', getattr(getattr(source_line, 'area', None), 'name', '演示区域'))}{line_number:02d}线"
        area_name = getattr(getattr(source_line, "area", None), "name", None) or getattr(source_line, "area_name", "")
        target_quantity = 800 + line_number * 120
        produced_quantity = target_quantity - (120 + line_number * 15)
        completion_rate = _percentage(produced_quantity, target_quantity)
        current_order_code = f"MO-{line_number:03d}"
        planned_start_at = timezone.localtime(current_time - timedelta(hours=2) + timedelta(hours=index))
        planned_end_at = planned_start_at + timedelta(hours=10 + (index % 4) * 3)
        remaining_quantity = max(target_quantity - produced_quantity, 0)
        standard_capacity_per_hour = _to_positive_decimal(
            runtime_parameters.get("defaultStandardCapacityPerHour"),
            Decimal(str(DEFAULT_RUNTIME_PARAMETERS["defaultStandardCapacityPerHour"])),
        )
        estimated_hours = Decimal(str(remaining_quantity)) / standard_capacity_per_hour
        if line_number % 4 == 0:
            estimated_hours += Decimal("20")
        estimated_completion_at = planned_start_at + timedelta(hours=float(estimated_hours))
        is_delayed = estimated_completion_at > planned_end_at
        total_target += target_quantity
        total_produced += produced_quantity
        line_summaries.append(
            {
                "lineCode": line_code,
                "lineName": line_name,
                "areaName": area_name,
                "currentOrderCode": current_order_code,
                "targetQuantity": target_quantity,
                "producedQuantity": produced_quantity,
                "completionRate": completion_rate,
                "plannedStartAt": planned_start_at.isoformat(),
                "plannedEndAt": planned_end_at.isoformat(),
                "estimatedCompletionAt": estimated_completion_at.isoformat(),
                "isDelayed": is_delayed,
                "display": _build_production_line_display(
                    current_order_code,
                    target_quantity,
                    produced_quantity,
                    completion_rate,
                    planned_start_at,
                    planned_end_at,
                    estimated_completion_at,
                    is_delayed,
                ),
            }
        )

    trend_points = []
    trend_window_hours = runtime_parameters["productionTrendWindowHours"]
    for offset in range(trend_window_hours):
        hour_label_time = timezone.localtime(current_time - timedelta(hours=trend_window_hours - offset - 1))
        hour_label = hour_label_time.strftime("%H:00")
        produced_quantity = 80 + offset * 7
        trend_points.append(
            {
                "hourLabel": hour_label,
                "producedQuantity": produced_quantity,
                "display": _build_production_trend_display(hour_label, produced_quantity),
            }
        )

    return {
        "total_target_quantity": total_target,
        "total_produced_quantity": total_produced,
        "overall_completion_rate": Decimal(str(_percentage(total_produced, total_target))),
        "line_summaries": line_summaries,
        "trend_points": trend_points,
        "generated_at": current_time,
        "source_updated_at": source_updated_at,
        "last_success_at": current_time,
    }


def _build_schedule_snapshot(current_time, source_updated_at, runtime_parameters: dict, production_snapshot: dict) -> dict:
    legend_items = [{"key": key, "label": item["label"], "color": item["color"]} for key, item in RISK_STATUS_DISPLAY.items()]
    line_schedules = []
    risk_counts = {"normal": 0, "warning": 0, "delayed": 0, "paused": 0}
    line_summaries = production_snapshot["line_summaries"]
    minimum_lines = max(
        len(line_summaries),
        int(runtime_parameters["autoScrollRowsThreshold"]) + 4,
        14,
    )

    for index in range(minimum_lines):
        line_number = index + 1
        source_summary = line_summaries[index % len(line_summaries)]
        source_area_name = source_summary.get("areaName") or "演示区域"
        line_code = source_summary["lineCode"] if index < len(line_summaries) else f"VIS-{line_number:02d}"
        line_name = source_summary["lineName"] if index < len(line_summaries) else f"{source_area_name}演示线 {line_number:02d}"

        order_count = 1 + (line_number % 3)
        orders = []
        cursor = current_time + timedelta(days=(index * 2) % 7)
        if line_number % 5 == 0:
            cursor -= timedelta(days=2)

        for order_index in range(order_count):
            order_number = order_index + 1
            risk_status = _resolve_mock_risk_status(line_number, order_number)
            duration_days = 1 + ((line_number + order_number) % 5)
            if order_number == order_count and line_number % 4 == 0:
                duration_days += 8

            planned_start = cursor
            planned_end = planned_start + timedelta(days=duration_days)
            display_start_at = planned_start.date().isoformat()
            display_end_at = planned_end.date().isoformat()
            completion_rate = max(18.0, min(98.0, float(source_summary["completionRate"]) - order_index * 7 + (index % 4) * 1.5))
            target_quantity = int(source_summary["targetQuantity"]) + order_index * 80 + index * 12
            produced_quantity = min(target_quantity, max(0, int(round(target_quantity * completion_rate / 100))))

            risk_counts[risk_status] += 1
            orders.append(
                {
                    "orderCode": f"PLAN-{line_number:03d}-{order_number}",
                    "materialCode": f"MAT-{line_number:03d}-{order_number}",
                    "status": "in_progress" if line_number == 1 and order_number == 1 else ("paused" if risk_status == "paused" else "planned"),
                    "riskStatus": risk_status,
                    "targetQuantity": target_quantity,
                    "producedQuantity": produced_quantity,
                    "plannedStartAt": planned_start.isoformat(),
                    "plannedEndAt": planned_end.isoformat(),
                    "displayStartAt": display_start_at,
                    "displayEndAt": display_end_at,
                    "completionRate": round(completion_rate, 2),
                    "display": _build_schedule_order_display(
                        risk_status,
                        display_start_at,
                        display_end_at,
                        round(completion_rate, 2),
                    ),
                }
            )
            cursor = planned_end + timedelta(days=1 if order_number % 2 == 1 else 0)

        line_schedules.append(
            {
                "lineCode": line_code,
                "lineName": line_name,
                "areaName": source_area_name,
                "orders": orders,
            }
        )

    return {
        "line_schedules": line_schedules,
        "risk_summary": {
            "windowDays": runtime_parameters["ganttWindowDays"],
            "counts": risk_counts,
        },
        "legend_items": legend_items,
        "generated_at": current_time,
        "source_updated_at": source_updated_at,
        "last_success_at": current_time,
    }


def _build_energy_snapshot(current_time, source_updated_at) -> dict:
    areas = list(Area.objects.filter(is_active=True).order_by("code"))
    if not areas:
        areas = [
            _FallbackArea("A01", "总装区"),
            _FallbackArea("A02", "包装区"),
            _FallbackArea("A03", "仓储区"),
        ]

    minimum_areas = max(len(areas), 8)
    total_consumption = Decimal("0.00")
    area_summaries = []
    for index in range(minimum_areas):
        source_area = areas[index % len(areas)]
        area_number = index + 1
        area_code = source_area.code if index < len(areas) else f"MOCK-A{area_number:02d}"
        area_name = source_area.name if index < len(areas) else f"{source_area.name}{area_number:02d}区"
        consumption = Decimal(str(480 + area_number * 65)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_consumption += consumption
        area_summaries.append(
            {
                "areaCode": area_code,
                "areaName": area_name,
                "consumption": str(consumption),
                "unit": "kWh",
                "display": _build_energy_area_display(str(consumption), "kWh"),
            }
        )

    return {
        "total_consumption": total_consumption,
        "unit": "kWh",
        "area_summaries": area_summaries,
        "generated_at": current_time,
        "source_updated_at": source_updated_at,
        "last_success_at": current_time,
    }


def _resolve_area(area_code: str | None):
    if not area_code:
        raise ValueError("area_code is required")
    area = Area.objects.filter(code=area_code, is_active=True).first()
    if not area:
        raise ValueError(f"area '{area_code}' not found or inactive")
    return area


def _apply_screen_page_bindings(base: dict, config: "ScreenConfig | None") -> dict:
    """
    大屏输出的 pageKeys / pageBindings 生成逻辑：
    1. 页面顺序：取 ScreenConfig.page_order（若非空）；否则回退 DEFAULT_SCREEN_CONFIGS 内置顺序。
    2. 数据源配置：从全局 ScreenPageBinding 按 screen_key + page_key 查询（不区分区域）。
    3. 仅将启用的绑定行插入 pageBindings；未启用的页面仍在 pageKeys 中（由前端渲染空壳）。
    """
    screen_key = base.get("screenKey")
    if not screen_key:
        raise ValueError("screenKey is required in screen config dict")

    # 确定轮播顺序
    page_order = (config.page_order if config else None) or []
    if not page_order:
        defaults = DEFAULT_SCREEN_CONFIGS.get(screen_key) or DEFAULT_SCREEN_CONFIGS["left"]
        page_order = list(defaults["pageKeys"])

    # 全局数据源配置（不过滤 area）
    bindings_qs = ScreenPageBinding.objects.filter(screen_key=screen_key, is_enabled=True)
    bindings_map = {b.page_key: b for b in bindings_qs}

    out = dict(base)
    out["pageKeys"] = list(page_order)
    out["pageBindings"] = [
        {
            "pageKey": b.page_key,
            "bindingSourceType": b.binding_source_type or None,
            "dataSourceIds": list(b.data_source_ids or []),
        }
        for pk in page_order
        if (b := bindings_map.get(pk)) is not None
    ]
    return out


def _get_screen_config(screen_key: str, area) -> dict:
    config = (
        ScreenConfig.objects.filter(area=area, screen_key=screen_key, is_active=True)
        .select_related("area")
        .first()
    )
    if not config:
        config = ScreenConfig.objects.filter(area__isnull=True, screen_key=screen_key, is_active=True).first()
    if not config:
        base = dict(DEFAULT_SCREEN_CONFIGS[screen_key])
        base["areaCode"] = area.code
        base["areaName"] = area.name
        return _apply_screen_page_bindings(base, None)
    merged = {
        "areaCode": area.code,
        "areaName": area.name,
        "screenKey": config.screen_key,
        "title": config.title,
        "subtitle": config.subtitle,
        "rotationIntervalSeconds": config.rotation_interval_seconds,
        "moduleSettings": config.module_settings,
        "themeSettings": config.theme_settings,
        "isActive": config.is_active,
    }
    return _apply_screen_page_bindings(merged, config)


def _get_display_content() -> dict:
    config = DisplayContentConfig.objects.filter(is_active=True).order_by("config_key").first()
    if not config:
        return DEFAULT_DISPLAY_CONTENT
    return {
        "configKey": config.config_key,
        "companyName": _coalesce_display_text(config.company_name, DEFAULT_DISPLAY_CONTENT["companyName"]),
        "welcomeMessage": _coalesce_display_text(config.welcome_message, DEFAULT_DISPLAY_CONTENT["welcomeMessage"]),
        "logoUrl": config.logo_url,
        "promoImageUrls": config.promo_image_urls,
        "isActive": config.is_active,
    }


def _get_runtime_parameters() -> dict:
    config = RuntimeParameterConfig.objects.filter(is_active=True).order_by("config_key").first()
    if not config:
        return DEFAULT_RUNTIME_PARAMETERS
    default_standard_capacity_per_hour = _to_positive_decimal(
        config.default_standard_capacity_per_hour,
        Decimal(str(DEFAULT_RUNTIME_PARAMETERS["defaultStandardCapacityPerHour"])),
    )
    gantt_window_days = _to_positive_int(config.gantt_window_days, DEFAULT_RUNTIME_PARAMETERS["ganttWindowDays"])
    auto_scroll_rows_threshold = _to_positive_int(
        config.auto_scroll_rows_threshold,
        DEFAULT_RUNTIME_PARAMETERS["autoScrollRowsThreshold"],
    )
    recent_capacity_window_hours = _to_positive_int(
        config.recent_capacity_window_hours,
        DEFAULT_RUNTIME_PARAMETERS["recentCapacityWindowHours"],
    )
    production_trend_window_hours = _to_positive_int(
        config.production_trend_window_hours,
        DEFAULT_RUNTIME_PARAMETERS["productionTrendWindowHours"],
    )

    return {
        "configKey": config.config_key,
        "singleDayEffectiveWorkHours": str(config.single_day_effective_work_hours),
        "defaultStandardCapacityPerHour": str(default_standard_capacity_per_hour),
        "delayWarningBufferHours": str(config.delay_warning_buffer_hours),
        "ganttWindowDays": gantt_window_days,
        "autoScrollEnabled": config.auto_scroll_enabled,
        "autoScrollRowsThreshold": auto_scroll_rows_threshold,
        "recentCapacityWindowHours": recent_capacity_window_hours,
        "productionTrendWindowHours": production_trend_window_hours,
        "notes": config.notes,
        "isActive": config.is_active,
    }


def _get_health_statuses() -> list[dict]:
    statuses = DataSourceHealthSnapshot.objects.order_by("source_key")
    return DataSourceHealthSnapshotSerializer(statuses, many=True).data


def _build_area_device_overview(area) -> dict:
    devices = list(Device.objects.filter(is_active=True, area=area))
    status_breakdown = {
        Device.STATUS_RUNNING: 0,
        Device.STATUS_STOPPED: 0,
        Device.STATUS_ALARM: 0,
        Device.STATUS_OFFLINE: 0,
    }
    for device in devices:
        status_breakdown[device.default_status] = status_breakdown.get(device.default_status, 0) + 1
    total_count = len(devices)
    running_count = status_breakdown.get(Device.STATUS_RUNNING, 0)
    abnormal_count = max(total_count - running_count, 0)
    return {
        "total_count": total_count,
        "running_count": running_count,
        "abnormal_count": abnormal_count,
        "status_breakdown": status_breakdown,
    }


TK_NODE_COMMENT_MAP = {
    "/Channel/State/chanStatus": "机床运行状态",
    "/Nck/Configuration/nckVersion": "CNC型号",
    "/Nck/Configuration/nckType": "CNC类型",
    "/Nck/State/hwProductSerialNr[1]": "序列号(CF卡)",
    "/Nck/Configuration/maxnumGlobMachAxes": "最大轴数",
    "/Nck/Configuration/numGlobMachAxes": "有效轴数",
    "/Channel/Configuration/numSpindles[u1, 1]": "主轴数",
    "/Channel/LogicalSpindle/acSmaxVelo[u1, 1]": "主轴最高转速",
    "/Channel/State/progStatus[u1]": "CNC状态",
    "/Bag/State/opMode[u1]": "工作模式",
    "/Nck/MachineAxis/status[1]": "轴移动状态",
    "/Channel/ProgramInfo/selectedWorkPProg[u1, 1]": "主程序号",
    "/Channel/ProgramInfo/progName[u1]": "子程序号",
    "/Channel/ProgramInfo/blockNoStr[u1]": "执行行号(字符串)",
    "/Channel/ProgramInfo/actLineNumber[u1, 1]": "执行行号(数值)",
    "/Channel/ProgramInfo/actBlock[u1, 1]": "执行代码",
    "/Channel/ChannelDiagnose/cycleTime[u1, 1]": "切削时间",
    "/Channel/ChannelDiagnose/operatingTime[u1, 1]": "程序加工时间",
    "/Nck/ChannelDiagnose/setupTime[1]": "系统累计开机时间",
    "/Channel/GeometricAxis/feedRateOvr[u1, 1]": "切削倍率",
    "/Channel/Spindle/speedOvr[u1, 1]": "主轴倍率",
    "/Channel/GeometricAxis/cmdFeedRate[u1, 1]": "切削指定速度F",
    "/Channel/GeometricAxis/actFeedRate[u1, 1]": "切削实际速度",
    "/Channel/Spindle/cmdSpeed[u1, 1]": "主轴指定速度S",
    "/Nck/Spindle/driveLoad": "主轴负载",
    "/Nck/Spindle/driveLoad[u1, 1]": "主轴负载",
    "/DriveVsa/Drive/r0035": "主轴电机温度",
    "/Channel/Spindle/actSpeed[u1, 1]": "主轴实际速度",
    "/Channel/Drive/AXCONF_CHANAX_NAME_TAB[1]": "轴名称",
    "/Channel/MachineAxis/actToolBasePos[u1, 1]": "机械坐标",
    "/Channel/GeometricAxis/actToolBasePos[u1, 1]": "绝对编程坐标",
    "/Nck/State/numAlarms": "报警数量",
    "/Nck/SequencedAlarms/clearInfo[1]": "报警类型",
    "/Nck/SequencedAlarms/textIndex[1]": "报警号",
}

TK_NODE_GROUP_MAP = {
    "/Channel/State/chanStatus": ("runtime", "运行状态"),
    "/Channel/State/progStatus[u1]": ("runtime", "运行状态"),
    "/Bag/State/opMode[u1]": ("runtime", "运行状态"),
    "/Nck/MachineAxis/status[1]": ("runtime", "运行状态"),
    "/Channel/ProgramInfo/selectedWorkPProg[u1, 1]": ("program", "程序信息"),
    "/Channel/ProgramInfo/progName[u1]": ("program", "程序信息"),
    "/Channel/ProgramInfo/blockNoStr[u1]": ("program", "程序信息"),
    "/Channel/ProgramInfo/actLineNumber[u1, 1]": ("program", "程序信息"),
    "/Channel/ProgramInfo/actBlock[u1, 1]": ("program", "程序信息"),
    "/Channel/ChannelDiagnose/cycleTime[u1, 1]": ("timer", "加工计时"),
    "/Channel/ChannelDiagnose/operatingTime[u1, 1]": ("timer", "加工计时"),
    "/Nck/ChannelDiagnose/setupTime[1]": ("timer", "加工计时"),
    "/Channel/GeometricAxis/feedRateOvr[u1, 1]": ("speed", "速度与倍率"),
    "/Channel/Spindle/speedOvr[u1, 1]": ("speed", "速度与倍率"),
    "/Channel/GeometricAxis/cmdFeedRate[u1, 1]": ("speed", "速度与倍率"),
    "/Channel/GeometricAxis/actFeedRate[u1, 1]": ("speed", "速度与倍率"),
    "/Channel/Spindle/cmdSpeed[u1, 1]": ("speed", "速度与倍率"),
    "/Channel/Spindle/actSpeed[u1, 1]": ("speed", "速度与倍率"),
    "/Nck/Spindle/driveLoad": ("spindle", "主轴"),
    "/Nck/Spindle/driveLoad[u1, 1]": ("spindle", "主轴"),
    "/DriveVsa/Drive/r0035": ("spindle", "主轴"),
    "/Channel/MachineAxis/actToolBasePos[u1, 1]": ("coordinate", "坐标信息"),
    "/Channel/GeometricAxis/actToolBasePos[u1, 1]": ("coordinate", "坐标信息"),
    "/Nck/State/numAlarms": ("alarm", "报警信息"),
    "/Nck/SequencedAlarms/clearInfo[1]": ("alarm", "报警信息"),
    "/Nck/SequencedAlarms/textIndex[1]": ("alarm", "报警信息"),
}

BASIC_INFO_NODE_PATHS = {
    "/Nck/Configuration/nckVersion",
    "/Nck/Configuration/nckType",
    "/Nck/State/hwProductSerialNr[1]",
    "/Nck/Configuration/maxnumGlobMachAxes",
    "/Nck/Configuration/numGlobMachAxes",
    "/Channel/Configuration/numSpindles[u1, 1]",
    "/Channel/LogicalSpindle/acSmaxVelo[u1, 1]",
    "/Channel/Drive/AXCONF_CHANAX_NAME_TAB[1]",
}


def _resolve_node_comment(node_item: dict, index: int) -> str:
    explicit = (node_item.get("comment") or "").strip()
    if explicit:
        return explicit
    node_id = (node_item.get("nodeId") or "").strip()
    path_key = node_id.removeprefix("ns=2;s=")
    mapped = TK_NODE_COMMENT_MAP.get(path_key)
    if mapped:
        return mapped
    if path_key.startswith("/Nck/Spindle/driveLoad"):
        return "主轴负载"
    return f"参数{index}"


def _resolve_node_group(node_item: dict) -> tuple[str, str]:
    node_id = (node_item.get("nodeId") or "").strip()
    path_key = node_id.removeprefix("ns=2;s=")
    if "ns=4" in path_key or path_key.startswith("ns=4"):
        return ("robot", "机器人")
    mapped = TK_NODE_GROUP_MAP.get(path_key)
    if mapped:
        return mapped
    if path_key.startswith("/Nck/Spindle/driveLoad"):
        return ("spindle", "主轴")
    return ("other", "其他参数")


def _is_basic_info_node(node_item: dict) -> bool:
    node_id = (node_item.get("nodeId") or "").strip()
    path_key = node_id.removeprefix("ns=2;s=")
    return path_key in BASIC_INFO_NODE_PATHS


# TK.MD §3 运行状态 — 数值含义（镗床 NS2）
_PROG_STATUS_MEANING = {
    1: "中断",
    2: "停止",
    3: "运行",
    4: "等待",
    5: "中止",
}
_OP_MODE_MEANING = {
    0: "JOG手动",
    1: "MDI",
    2: "AUTO自动",
}
_AXIS_MOVE_STATUS_MEANING = {
    0: "正向移动",
    1: "负向移动",
    2: "粗到位",
    3: "精到位",
}


def _coerce_mapping_int(value) -> int | None:
    """Best-effort convert OPC UA scalar to int for TK enum lookup."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        try:
            f = float(s)
            if f.is_integer():
                return int(f)
        except ValueError:
            return None
        return None
    return None


def _map_runtime_status_display(path_key: str, raw_value) -> str:
    """
    Map runtime-group numeric codes to labels defined in docs/TK.MD.
    Unknown paths or non-integer values fall back to str(raw_value).
    """
    if raw_value is None:
        return "--"
    n = _coerce_mapping_int(raw_value)
    if n is None:
        return str(raw_value)

    if path_key.startswith("/Channel/State/progStatus["):
        return _PROG_STATUS_MEANING.get(n, str(raw_value))
    if path_key.startswith("/Bag/State/opMode["):
        return _OP_MODE_MEANING.get(n, str(raw_value))
    if path_key.startswith("/Nck/MachineAxis/status["):
        return _AXIS_MOVE_STATUS_MEANING.get(n, str(raw_value))

    return str(raw_value)


def _display_parameter_value(node_id: str, group_key: str, ok: bool, raw_value) -> str:
    if not ok:
        return "--"
    path_key = (node_id or "").strip().removeprefix("ns=2;s=")
    if "ns=4" in path_key and group_key == "robot":
        return str(raw_value) if raw_value is not None else "--"
    if group_key == "runtime":
        return _map_runtime_status_display(path_key, raw_value)
    return raw_value if raw_value is not None else "--"


_RE_PROG_STATUS_PATH = re.compile(r"^/Channel/State/progStatus\[u\d+\]")
_RE_SP_ACT_PATH = re.compile(r"^/Channel/Spindle/actSpeed\[u(\d+),\s*(\d+)\]")
_RE_SP_OVR_PATH = re.compile(r"^/Channel/Spindle/speedOvr\[u(\d+),\s*(\d+)\]")
_RE_SP_CMD_PATH = re.compile(r"^/Channel/Spindle/cmdSpeed\[u(\d+),\s*(\d+)\]")
_RE_NCK_SP_DRIVE_LOAD_PATH = re.compile(r"^/Nck/Spindle/driveLoad\[u(\d+),\s*(\d+)\]")


def _opcua_node_path(node_id: str) -> str:
    return (node_id or "").strip().removeprefix("ns=2;s=")


def _build_opcua_value_map(read_items) -> dict[str, tuple[bool, object]]:
    """Map browse path -> (ok, raw_value). OpcUa layer stores values as strings."""
    out: dict[str, tuple[bool, object]] = {}
    for item in read_items:
        pk = _opcua_node_path(item.node_id)
        out[pk] = (item.ok, item.value)
    return out


def _parse_numeric_scalar(raw) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    s = str(raw).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int_scalar(raw) -> int | None:
    n = _parse_numeric_scalar(raw)
    if n is None:
        return None
    try:
        return int(round(n))
    except (OverflowError, ValueError):
        return None


def _format_seconds_hms(sec_val) -> str:
    if sec_val is None:
        return "--"
    try:
        sec = int(round(float(str(sec_val).strip())))
    except (ValueError, TypeError):
        return "--"
    sec = max(sec, 0)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _discover_channel_index(vm: dict[str, tuple[bool, object]]) -> int:
    channels: list[int] = []
    for key in vm:
        m = _RE_SP_ACT_PATH.match(key)
        if m:
            channels.append(int(m.group(1)))
            continue
        m = _RE_NCK_SP_DRIVE_LOAD_PATH.match(key)
        if m:
            channels.append(int(m.group(1)))
            continue
        m = re.match(r"^/Channel/State/progStatus\[u(\d+)\]", key)
        if m:
            channels.append(int(m.group(1)))
            continue
        m = re.match(r"^/Bag/State/opMode\[u(\d+)\]", key)
        if m:
            channels.append(int(m.group(1)))
    return min(channels) if channels else 1


def _extract_cnc_state(vm: dict[str, tuple[bool, object]]) -> int | None:
    for key, (ok, val) in vm.items():
        if ok and _RE_PROG_STATUS_PATH.match(key):
            return _parse_int_scalar(val)
    return None


def _extract_alarm_nums(vm: dict[str, tuple[bool, object]]) -> int | None:
    t = vm.get("/Nck/State/numAlarms")
    if not t or not t[0]:
        return None
    return _parse_int_scalar(t[1])


def _extract_device_model(vm: dict[str, tuple[bool, object]]) -> str:
    t = vm.get("/Nck/Configuration/nckVersion")
    if not t or not t[0]:
        return "--"
    val = t[1]
    num = _parse_numeric_scalar(val)
    if num is None:
        s = str(val).strip()
        return s if s else "--"
    if abs(num - round(num)) < 1e-9:
        return str(int(round(num)))
    return f"{num:g}"


def _get_metric(vm: dict[str, tuple[bool, object]], pattern: re.Pattern, channel: int, row: int):
    for key, (ok, val) in vm.items():
        if not ok:
            continue
        m = pattern.match(key)
        if m and int(m.group(1)) == channel and int(m.group(2)) == row:
            return val
    return None


def _get_nck_spindle_drive_load_pct(
    vm: dict[str, tuple[bool, object]], channel: int, row: int
) -> float | None:
    """
    NCK 主轴驱动负载（828D/840D sl），常见 Browse：
    /Nck/Spindle/driveLoad 或 /Nck/Spindle/driveLoad[u<Area>,<Row>]（百分比）。
    """
    raw = _get_metric(vm, _RE_NCK_SP_DRIVE_LOAD_PATH, channel, row)
    if raw is not None:
        v = _parse_numeric_scalar(raw)
        if v is not None:
            return v
    t = vm.get("/Nck/Spindle/driveLoad")
    if t and t[0]:
        return _parse_numeric_scalar(t[1])
    return None


def _get_sinamics_spindle_motor_temp_c(vm: dict[str, tuple[bool, object]]) -> float | None:
    """
    828D/840D sl — SINAMICS 主轴电机温度，Browse: /DriveVsa/Drive/r0035（单位 °C）。
    """
    for path in ("/DriveVsa/Drive/r0035",):
        t = vm.get(path)
        if t and t[0]:
            return _parse_numeric_scalar(t[1])
    return None


def _percent_from_override(raw) -> float | None:
    """Siemens speed override may be 1.0 (=100%) or 100."""
    num = _parse_numeric_scalar(raw)
    if num is None:
        return None
    if num <= 2.0:
        return round(num * 100.0, 1)
    return round(num, 1)


def _resolve_machine_panel_status(
    offline: bool,
    cnc_state: int | None,
    alarm_nums: int | None,
) -> dict:
    """
    UI status for CNC dashboard (TK.MD + alarm count).
    Border colors: green / yellow / red / gray.
    """
    if offline:
        return {
            "code": "offline",
            "label": "离线",
            "borderColor": "gray",
            "alarmActive": False,
            "indicator": "gray",
        }
    alarms = alarm_nums if alarm_nums is not None else 0
    if alarms > 0 or cnc_state in (1, 5):
        return {
            "code": "alarm",
            "label": "报警",
            "borderColor": "red",
            "alarmActive": True,
            "indicator": "red",
        }
    if cnc_state == 3:
        return {
            "code": "running",
            "label": "运行中",
            "borderColor": "green",
            "alarmActive": False,
            "indicator": "green",
        }
    if cnc_state in (2, 4):
        return {
            "code": "standby",
            "label": "待机",
            "borderColor": "yellow",
            "alarmActive": False,
            "indicator": "yellow",
        }
    return {
        "code": "standby",
        "label": "待机",
        "borderColor": "yellow",
        "alarmActive": False,
        "indicator": "yellow",
    }


def _work_mode_short(op_raw) -> str:
    n = _parse_int_scalar(op_raw)
    if n is None:
        return "--"
    return {0: "JOG", 1: "MDI", 2: "AUTO"}.get(n, "--")


def _find_first_matching(vm: dict[str, tuple[bool, object]], prefixes: tuple[str, ...]) -> object | None:
    for key, (ok, val) in vm.items():
        if not ok:
            continue
        if any(key.startswith(p) for p in prefixes):
            return val
    return None


def _extract_exe_line(vm: dict[str, tuple[bool, object]], channel: int) -> str:
    block_prefix = f"/Channel/ProgramInfo/blockNoStr[u{channel}]"
    block = _find_first_matching(vm, (block_prefix,))
    if block is not None and str(block).strip():
        return str(block).strip()
    line_prefix = f"/Channel/ProgramInfo/actLineNumber[u{channel},"
    line = _find_first_matching(vm, (line_prefix,))
    if line is not None and str(line).strip():
        return str(line).strip()
    return "--"


def _build_cnc_dashboard_view(
    vm: dict[str, tuple[bool, object]],
    *,
    offline: bool,
    device_model_fallback: str,
) -> dict:
    channel = _discover_channel_index(vm)
    cnc_state = None if offline else _extract_cnc_state(vm)
    alarm_nums = None if offline else _extract_alarm_nums(vm)
    model = "--" if offline else _extract_device_model(vm)
    if model == "--" and device_model_fallback:
        model = device_model_fallback

    ms = _resolve_machine_panel_status(offline, cnc_state, alarm_nums)

    def _fill_current_spindle_slot(row_index: int, label: str, *, configured: bool) -> dict:
        slot = {
            "label": label,
            "configured": configured,
            "actSpeedRpm": None,
            "cmdSpeedRpm": None,
            "speedOverridePct": None,
            "temperatureC": None,
            "loadPct": None,
        }
        if configured:
            act_raw = _get_metric(vm, _RE_SP_ACT_PATH, channel, row_index)
            cmd_raw = _get_metric(vm, _RE_SP_CMD_PATH, channel, row_index)
            ovr_raw = _get_metric(vm, _RE_SP_OVR_PATH, channel, row_index)
            slot["actSpeedRpm"] = _parse_numeric_scalar(act_raw)
            slot["cmdSpeedRpm"] = _parse_numeric_scalar(cmd_raw)
            slot["speedOverridePct"] = _percent_from_override(ovr_raw)
            slot["temperatureC"] = _get_sinamics_spindle_motor_temp_c(vm)
            slot["loadPct"] = _get_nck_spindle_drive_load_pct(vm, channel, row_index)
        return slot

    spindle_slots = [_fill_current_spindle_slot(1, "主轴", configured=not offline)]

    main_prog = "--"
    raw_prog = _find_first_matching(vm, ("/Channel/ProgramInfo/selectedWorkPProg[",))
    if raw_prog is not None and str(raw_prog).strip():
        main_prog = str(raw_prog).strip()

    op_raw = next(
        (
            val
            for key, (ok, val) in vm.items()
            if ok and key.startswith("/Bag/State/opMode[")
        ),
        None,
    )

    cyc = None if offline else _find_first_matching(vm, ("/Channel/ChannelDiagnose/cycleTime[",))
    op_time = None if offline else _find_first_matching(vm, ("/Channel/ChannelDiagnose/operatingTime[",))

    return {
        "deviceModel": model,
        "machineStatus": {
            **ms,
            "cncState": cnc_state,
            "alarmNums": alarm_nums,
        },
        "spindles": spindle_slots,
        "job": {
            "mainProgram": main_prog,
            "exeLine": "--" if offline else _extract_exe_line(vm, channel),
            "cycleTimeFormatted": "--" if offline else _format_seconds_hms(cyc),
            "operationTimeFormatted": "--" if offline else _format_seconds_hms(op_time),
            "workModeTag": "--" if offline else _work_mode_short(op_raw),
        },
    }


def _normalize_opcua_node_config(source: DataSourceConfig) -> list[dict]:
    node_config_raw = source.node if isinstance(source.node, list) else []
    node_config: list[dict] = []
    for cfg_item in node_config_raw:
        if isinstance(cfg_item, str):
            node_config.append({"nodeId": cfg_item, "comment": ""})
        elif isinstance(cfg_item, dict):
            node_config.append(cfg_item)
    return node_config


def _classify_opcua_data_source(source: DataSourceConfig) -> str:
    """
    机器人：节点主要为 NS4；镗床/CNC：NS2 等。混配时按镗床处理。
    """
    seen_ns2 = False
    seen_ns4 = False
    for cfg in _normalize_opcua_node_config(source):
        nid = (cfg.get("nodeId") or "").strip().lower()
        if "ns=4" in nid:
            seen_ns4 = True
        if "ns=2" in nid:
            seen_ns2 = True
    if seen_ns4 and not seen_ns2:
        return "robot"
    return "cnc"


def _production_line_for_source(source: DataSourceConfig, area) -> ProductionLine | None:
    d = (
        source.devices.filter(area=area, is_active=True)
        .select_related("production_line")
        .order_by("code")
        .first()
    )
    if d and d.production_line_id:
        return d.production_line
    return None


def _build_opcua_realtime_card_payload(source: DataSourceConfig, area) -> dict:
    """单 OPC 数据源一张卡（镗床/CNC 仪表盘结构）。"""
    card_devices = list(source.devices.filter(area=area, is_active=True).order_by("code")[:2])
    card_name = ", ".join([f"{d.code}-{d.name}" for d in card_devices]) or source.name
    display_title = card_devices[0].name if len(card_devices) == 1 else card_name
    node_config = _normalize_opcua_node_config(source)
    base_ts = timezone.localtime().isoformat()

    def _empty_detail_payload(reason: str, *, offline: bool) -> dict:
        vm_empty: dict[str, tuple[bool, object]] = {}
        dash = _build_cnc_dashboard_view(
            vm_empty,
            offline=offline,
            device_model_fallback="",
        )
        return {
            "sourceCode": source.code,
            "sourceName": source.name,
            "deviceName": display_title,
            "displayTitle": display_title,
            "subtitle": card_name if card_name != display_title else "",
            "mergeLayout": False,
            "status": "offline" if offline else "online",
            "offlineReason": reason,
            "updatedAt": base_ts,
            "parameters": [],
            "groupedParameters": [],
            **dash,
        }

    if not node_config:
        return _empty_detail_payload("未配置 OPC UA 节点列表", offline=True)

    read_result = read_opcua_nodes(source.connection_config or {}, node=node_config)
    vm = _build_opcua_value_map(read_result.items)
    data_offline = bool(read_result.offline or len(read_result.items) == 0)
    offline_reason = ""
    if read_result.offline:
        offline_reason = read_result.message or "连接超时或无法建立连接"
    elif len(read_result.items) == 0:
        offline_reason = "未配置可读取节点"

    dash = _build_cnc_dashboard_view(
        vm,
        offline=data_offline,
        device_model_fallback="",
    )

    parameters = []
    grouped = {}
    for index, node_item in enumerate(read_result.items, start=1):
        item_group_key, item_group_label = _resolve_node_group({"nodeId": node_item.node_id})
        resolved_comment = _resolve_node_comment({"comment": node_item.comment, "nodeId": node_item.node_id}, index)
        display_val = _display_parameter_value(node_item.node_id, item_group_key, node_item.ok, node_item.value)
        parameters.append(
            {
                "comment": resolved_comment,
                "groupKey": item_group_key,
                "groupLabel": item_group_label,
                "value": display_val,
                "ok": node_item.ok,
                "error": node_item.error,
            }
        )
        grouped.setdefault(
            item_group_key,
            {
                "groupKey": item_group_key,
                "groupLabel": item_group_label,
                "items": [],
            },
        )
        grouped[item_group_key]["items"].append(
            {
                "comment": resolved_comment,
                "value": display_val,
                "ok": node_item.ok,
                "error": node_item.error,
            }
        )

    online = not data_offline
    return {
        "sourceCode": source.code,
        "sourceName": source.name,
        "deviceName": display_title,
        "displayTitle": display_title,
        "subtitle": card_name if card_name != display_title else "",
        "mergeLayout": False,
        "status": "online" if online else "offline",
        "offlineReason": offline_reason,
        "updatedAt": base_ts,
        "parameters": parameters,
        "groupedParameters": list(grouped.values()),
        **dash,
    }


def _build_robot_realtime_panel(source: DataSourceConfig | None, area) -> dict:
    """机器人 NS4 节点列表 — 注释 + 原始值。"""
    base_ts = timezone.localtime().isoformat()
    if not source:
        return {
            "displayTitle": "",
            "status": "offline",
            "offlineReason": "未绑定机器人数据源",
            "items": [],
            "updatedAt": base_ts,
        }

    rdev = source.devices.filter(area=area, is_active=True).order_by("code").first()
    display_title = rdev.name if rdev else source.name
    node_config = _normalize_opcua_node_config(source)
    if not node_config:
        return {
            "displayTitle": display_title,
            "status": "offline",
            "offlineReason": "未配置机器人 OPC 节点",
            "items": [],
            "updatedAt": base_ts,
        }

    read_result = read_opcua_nodes(source.connection_config or {}, node=node_config)
    items = []
    for index, node_item in enumerate(read_result.items, start=1):
        resolved_comment = _resolve_node_comment({"comment": node_item.comment, "nodeId": node_item.node_id}, index)
        display_val = str(node_item.value) if node_item.ok else "--"
        items.append(
            {
                "comment": resolved_comment,
                "value": display_val,
                "ok": node_item.ok,
                "error": node_item.error,
            }
        )

    data_offline = bool(read_result.offline or len(read_result.items) == 0)
    offline_reason = ""
    if read_result.offline:
        offline_reason = read_result.message or "连接超时或无法建立连接"
    elif len(read_result.items) == 0:
        offline_reason = "未配置可读取节点"

    return {
        "displayTitle": display_title,
        "status": "online" if not data_offline else "offline",
        "offlineReason": offline_reason,
        "items": items,
        "updatedAt": base_ts,
    }


def _empty_cnc_payload_for_merge(reason: str) -> dict:
    base_ts = timezone.localtime().isoformat()
    dash = _build_cnc_dashboard_view({}, offline=True, device_model_fallback="")
    return {
        "sourceCode": "",
        "sourceName": "",
        "deviceName": "",
        "displayTitle": "",
        "subtitle": "",
        "status": "offline",
        "offlineReason": reason,
        "updatedAt": base_ts,
        "parameters": [],
        "groupedParameters": [],
        **dash,
    }


def _merge_line_realtime_card(pl: ProductionLine, cnc_src: DataSourceConfig | None, robot_src: DataSourceConfig | None, area) -> dict:
    """同一产线下镗床 + 机器人并排数据源合并为一张卡。"""
    line_devices = list(Device.objects.filter(production_line_id=pl.pk, area=area, is_active=True).order_by("code"))
    cnc_dev = next((d for d in line_devices if "机器人" not in d.name), None)
    robot_dev = next((d for d in line_devices if "机器人" in d.name), None)
    display_title = (cnc_dev.name if cnc_dev else None) or (robot_dev.name if robot_dev else pl.name)
    sub_parts = []
    if cnc_src:
        sub_parts.append(cnc_src.name)
    if robot_src:
        sub_parts.append(robot_src.name)
    subtitle = " · ".join(sub_parts)

    cnc_card = (
        _build_opcua_realtime_card_payload(cnc_src, area) if cnc_src else _empty_cnc_payload_for_merge("未绑定镗床数据源")
    )
    robot_panel = _build_robot_realtime_panel(robot_src, area)

    cnc_ok = cnc_card.get("status") == "online"
    robot_ok = robot_panel.get("status") == "online"
    card_status = "online" if (cnc_ok or robot_ok) else "offline"
    reasons = []
    if not cnc_ok and cnc_card.get("offlineReason"):
        reasons.append(f"镗床: {cnc_card['offlineReason']}")
    if not robot_ok and robot_panel.get("offlineReason"):
        reasons.append(f"机器人: {robot_panel['offlineReason']}")
    merged_reason = "；".join(reasons)

    ms = cnc_card.get("machineStatus") or {}
    if not cnc_src and robot_src:
        ms = {
            "code": "offline",
            "label": "离线",
            "borderColor": "gray",
            "alarmActive": False,
            "indicator": "gray",
            "cncState": None,
            "alarmNums": None,
        }

    updated_candidates = [cnc_card.get("updatedAt", ""), robot_panel.get("updatedAt", "")]
    updated_at = max(updated_candidates) if updated_candidates else timezone.localtime().isoformat()

    return {
        **{k: v for k, v in cnc_card.items() if k not in ("sourceCode", "sourceName", "mergeLayout")},
        "sourceCode": f"LINE-{pl.code}",
        "sourceName": pl.name,
        "mergeLayout": True,
        "productionLineCode": pl.code,
        "displayTitle": display_title,
        "subtitle": subtitle,
        "deviceName": display_title,
        "robot": robot_panel,
        "status": card_status,
        "offlineReason": merged_reason if card_status != "online" else "",
        "cncSourceStatus": cnc_card.get("status"),
        "robotSourceStatus": robot_panel.get("status"),
        "machineStatus": ms,
        "updatedAt": updated_at,
    }


def _page_binding_data_source_ids(screen_config: dict, page_key: str) -> list[int]:
    """从 screen_config['pageBindings'] 取指定 page_key 的 dataSourceIds；无则返回空列表。"""
    for binding in screen_config.get("pageBindings") or []:
        if binding.get("pageKey") == page_key:
            ids = binding.get("dataSourceIds") or []
            return [i for i in ids if isinstance(i, int) and i > 0]
    return []


ENERGY_CATEGORY_LABELS = {
    1: "照明插座",
    2: "空调",
    3: "动力",
    4: "特殊",
}

ENERGY_CATEGORY_COLORS = {
    1: "#4ade80",
    2: "#38bdf8",
    3: "#fb923c",
    4: "#c084fc",
}


def _mysql_query_rows(connection_config: dict, sql: str, params=None) -> list[dict]:
    """Execute a SELECT against a MySQL datasource; return list of dicts."""
    try:
        import MySQLdb  # type: ignore
        import MySQLdb.cursors  # type: ignore
    except ImportError:
        raise RuntimeError("MySQLdb (mysqlclient) 未安装，无法查询能耗数据库")

    cc = connection_config
    conn = MySQLdb.connect(
        host=(cc.get("host") or "").strip(),
        port=int(cc.get("port") or 3306),
        user=(cc.get("username") or "").strip(),
        passwd=cc.get("password") or "",
        db=(cc.get("database") or "").strip(),
        charset="utf8mb4",
        connect_timeout=10,
        read_timeout=15,
    )
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(sql, params or ())
        return list(cur.fetchall())
    finally:
        conn.close()


def _safe_kwh(real_data, multiplying_power) -> Decimal:
    try:
        v = Decimal(str(real_data))
        if multiplying_power not in (None, "", "0"):
            v = v * Decimal(str(multiplying_power))
        return v
    except Exception:
        return Decimal("0")


def _build_energy_data_page(data_source_ids: list[int]) -> dict:
    """
    查询能耗平台数据库（po_day / po_month / platform_equipment），
    构建能耗数据页面载荷供前端渲染。

    data_source_ids 必须在屏幕子页面绑定中明确配置；为空时直接返回提示，
    不做全局 database 类型的兜底搜索，以免误连 WMS 等其他数据库。
    """
    if not data_source_ids:
        return _empty_energy_data_page("请在「屏幕子页面」中为能耗数据页面配置数据源")

    # 信任用户选择的 ID，不再限制 source_type（energy_db 或 database 均可）
    sources = list(
        DataSourceConfig.objects.filter(
            pk__in=data_source_ids,
            is_enabled=True,
        )
    )

    if not sources:
        return _empty_energy_data_page("配置的能耗数据源未找到或已禁用")

    source = sources[0]
    cc = source.connection_config or {}

    try:
        today_rows = _mysql_query_rows(
            cc,
            """
            SELECT
                e.p_e_name  AS equipment_name,
                e.p_e_code  AS equipment_code,
                d.energy_consumption,
                d.collection_name,
                d.real_data,
                d.multiplying_power,
                d.modify_time
            FROM po_day d
            LEFT JOIN platform_equipment e ON d.equipment_ids = e.e_id
            WHERE d.types = 1
              AND d.is_flag  = '0'
              AND d.del_flag = '0'
              AND DATE(d.create_time) = CURDATE()
            ORDER BY d.energy_consumption, e.p_e_code
            """,
        )
        month_agg_rows = _mysql_query_rows(
            cc,
            """
            SELECT
                d.energy_consumption,
                SUM(
                    COALESCE(CAST(NULLIF(d.real_data,'') AS DECIMAL(18,4)), 0)
                    * COALESCE(CAST(NULLIF(d.multiplying_power,'0') AS DECIMAL(10,4)), 1)
                ) AS total_kwh
            FROM po_month d
            WHERE d.types = 1
              AND d.is_flag  = '0'
              AND d.del_flag = '0'
              AND YEAR(d.create_time)  = YEAR(CURDATE())
              AND MONTH(d.create_time) = MONTH(CURDATE())
            GROUP BY d.energy_consumption
            """,
        )
    except Exception as exc:
        logger.exception("energy_data_page query failed: %s", exc)
        return _empty_energy_data_page(f"数据库查询失败: {exc}")

    # ── today's totals ─────────────────────────────────────────────────────
    today_total = Decimal("0")
    category_totals: dict[int, Decimal] = {}
    equipment_list: list[dict] = []

    for row in today_rows:
        kwh = _safe_kwh(row.get("real_data"), row.get("multiplying_power"))
        today_total += kwh
        cat = int(row.get("energy_consumption") or 0)
        category_totals[cat] = category_totals.get(cat, Decimal("0")) + kwh
        mt = row.get("modify_time")
        equipment_list.append(
            {
                "equipmentName": row.get("equipment_name") or row.get("equipment_code") or "未知设备",
                "equipmentCode": row.get("equipment_code") or "",
                "category": ENERGY_CATEGORY_LABELS.get(cat, "其他"),
                "categoryId": cat,
                "collectionName": row.get("collection_name") or "",
                "todayKwh": str(kwh.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "updatedAt": mt.isoformat() if hasattr(mt, "isoformat") else str(mt or ""),
            }
        )

    # ── monthly total ───────────────────────────────────────────────────────
    month_total = Decimal("0")
    for row in month_agg_rows:
        try:
            month_total += Decimal(str(row.get("total_kwh") or 0))
        except Exception:
            pass

    # ── category breakdown ──────────────────────────────────────────────────
    categories = []
    for cat_id, label in ENERGY_CATEGORY_LABELS.items():
        val = category_totals.get(cat_id, Decimal("0"))
        pct = int(val / today_total * 100) if today_total > 0 else 0
        categories.append(
            {
                "id": cat_id,
                "label": label,
                "color": ENERGY_CATEGORY_COLORS[cat_id],
                "kwh": str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "percent": pct,
            }
        )

    return {
        "todayKwh": str(today_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "monthKwh": str(month_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "unit": "kWh",
        "categories": categories,
        "equipmentList": equipment_list,
        "updatedAt": timezone.localtime().isoformat(),
        "sourceName": getattr(source, "name", None) or getattr(source, "code", ""),
    }


def _empty_energy_data_page(reason: str) -> dict:
    return {
        "todayKwh": "0.00",
        "monthKwh": "0.00",
        "unit": "kWh",
        "categories": [],
        "equipmentList": [],
        "updatedAt": timezone.localtime().isoformat(),
        "errorMessage": reason,
    }


def _build_device_realtime_monitor(area, data_source_ids: list[int] | None = None) -> dict:
    """
    构建设备实时监控卡片列表。

    data_source_ids：若非空，只加载这些 ID 对应的 OPC UA 数据源（来自 ScreenPageBinding 配置）；
    为空或 None 时，回退到按区域关联设备自动发现所有启用的 OPC UA 数据源。
    """
    if data_source_ids:
        enabled_sources = (
            DataSourceConfig.objects.filter(
                pk__in=data_source_ids, is_enabled=True, source_type="opcua"
            )
            .prefetch_related("devices__production_line")
            .distinct()
            .order_by("code")
        )
    else:
        enabled_sources = (
            DataSourceConfig.objects.filter(
                is_enabled=True, source_type="opcua", devices__area=area, devices__is_active=True
            )
            .prefetch_related("devices__production_line")
            .distinct()
            .order_by("code")
        )
    min_interval = None
    for source in enabled_sources:
        min_interval = source.refresh_interval_seconds if min_interval is None else min(min_interval, source.refresh_interval_seconds)

    by_line: dict[int, dict[str, list[DataSourceConfig]]] = defaultdict(lambda: {"cnc": [], "robot": []})
    consumed: set[int] = set()

    for source in enabled_sources:
        pl = _production_line_for_source(source, area)
        kind = _classify_opcua_data_source(source)
        if pl is None:
            continue
        by_line[pl.pk][kind].append(source)
        consumed.add(source.pk)

    merged_tasks: list[tuple[ProductionLine, DataSourceConfig | None, DataSourceConfig | None]] = []
    for pl in ProductionLine.objects.filter(pk__in=list(by_line.keys())):
        bucket = by_line[pl.pk]
        cnc_src = min(bucket["cnc"], key=lambda s: s.code) if bucket["cnc"] else None
        robot_src = min(bucket["robot"], key=lambda s: s.code) if bucket["robot"] else None
        if cnc_src or robot_src:
            merged_tasks.append((pl, cnc_src, robot_src))

    standalone_sources = [s for s in enabled_sources if s.pk not in consumed]

    cards = []
    futures = []

    max_workers = min(max(len(merged_tasks) + len(standalone_sources), 1), 12)

    def _fail_card() -> dict:
        return {
            "sourceCode": "unknown",
            "sourceName": "未知数据源",
            "deviceName": "未知设备",
            "displayTitle": "未知设备",
            "subtitle": "",
            "mergeLayout": False,
            "status": "offline",
            "offlineReason": "数据源读取异常",
            "updatedAt": timezone.localtime().isoformat(),
            "parameters": [],
            "groupedParameters": [],
            **_build_cnc_dashboard_view(
                {},
                offline=True,
                device_model_fallback="",
            ),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for pl, cnc_src, robot_src in merged_tasks:
            futures.append(executor.submit(_merge_line_realtime_card, pl, cnc_src, robot_src, area))
        for src in standalone_sources:
            futures.append(executor.submit(_build_opcua_realtime_card_payload, src, area))

        for future in concurrent.futures.as_completed(futures):
            try:
                cards.append(future.result())
            except Exception as exc:  # noqa: BLE001
                logger.exception("realtime monitor card build failed: %s", exc)
                cards.append(_fail_card())

    cards.sort(key=lambda item: item.get("sourceCode", ""))
    return {
        "pollIntervalSeconds": int(min_interval or 30),
        "cards": cards,
    }


def _refresh_device_runtime_statuses_if_needed() -> None:
    now = timezone.now()
    snapshot = DeviceStatusSnapshot.objects.filter(snapshot_key=SNAPSHOT_KEY_DEFAULT).first()
    if snapshot and snapshot.source_updated_at and (
        now - snapshot.source_updated_at
    ).total_seconds() < DEVICE_STATUS_REFRESH_INTERVAL_SECONDS:
        return
    global _DEVICE_STATUS_REFRESH_RUNNING, _DEVICE_STATUS_REFRESH_LAST_TRIGGERED_AT
    with _DEVICE_STATUS_REFRESH_LOCK:
        if _DEVICE_STATUS_REFRESH_RUNNING:
            return
        if _DEVICE_STATUS_REFRESH_LAST_TRIGGERED_AT and (
            now - _DEVICE_STATUS_REFRESH_LAST_TRIGGERED_AT
        ).total_seconds() < DEVICE_STATUS_REFRESH_INTERVAL_SECONDS:
            return
        _DEVICE_STATUS_REFRESH_RUNNING = True
        _DEVICE_STATUS_REFRESH_LAST_TRIGGERED_AT = now
    threading.Thread(
        target=_refresh_device_runtime_statuses_worker,
        name="device-runtime-status-refresh",
        daemon=True,
    ).start()


def _refresh_device_runtime_statuses_worker() -> None:
    global _DEVICE_STATUS_REFRESH_RUNNING
    close_old_connections()
    try:
        _refresh_device_runtime_statuses_sync()
    except Exception:  # noqa: BLE001 - background task should never break request path
        logger.exception("device runtime status refresh failed")
    finally:
        close_old_connections()
        with _DEVICE_STATUS_REFRESH_LOCK:
            _DEVICE_STATUS_REFRESH_RUNNING = False


def _refresh_device_runtime_statuses_sync() -> None:
    now = timezone.now()

    active_devices = list(Device.objects.filter(is_active=True).order_by("id"))
    if not active_devices:
        DeviceStatusSnapshot.objects.update_or_create(
            snapshot_key=SNAPSHOT_KEY_DEFAULT,
            defaults={
                "total_count": 0,
                "running_count": 0,
                "abnormal_count": 0,
                "status_breakdown": {
                    Device.STATUS_RUNNING: 0,
                    Device.STATUS_STOPPED: 0,
                    Device.STATUS_ALARM: 0,
                    Device.STATUS_OFFLINE: 0,
                },
                "generated_at": now,
                "source_updated_at": now,
                "last_success_at": now,
            },
        )
        return

    device_ids = [device.id for device in active_devices]
    enabled_sources = (
        DataSourceConfig.objects.filter(is_enabled=True, devices__id__in=device_ids)
        .prefetch_related("devices")
        .distinct()
    )
    source_result_cache = {}
    device_has_running_source = {device_id: False for device_id in device_ids}

    for source in enabled_sources:
        source_ok = source_result_cache.get(source.id)
        if source_ok is None:
            source_ok = _test_data_source_connectivity(source)
            source_result_cache[source.id] = source_ok
        if not source_ok:
            continue
        for bound_device in source.devices.all():
            if bound_device.id in device_has_running_source:
                device_has_running_source[bound_device.id] = True

    changed_devices = []
    for device in active_devices:
        target_status = Device.STATUS_RUNNING if device_has_running_source.get(device.id, False) else Device.STATUS_STOPPED
        if device.default_status != target_status:
            device.default_status = target_status
            changed_devices.append(device)
    if changed_devices:
        Device.objects.bulk_update(changed_devices, ["default_status"])

    running_count = sum(1 for device in active_devices if device_has_running_source.get(device.id, False))
    total_count = len(active_devices)
    abnormal_count = total_count - running_count
    DeviceStatusSnapshot.objects.update_or_create(
        snapshot_key=SNAPSHOT_KEY_DEFAULT,
        defaults={
            "total_count": total_count,
            "running_count": running_count,
            "abnormal_count": abnormal_count,
            "status_breakdown": {
                Device.STATUS_RUNNING: running_count,
                Device.STATUS_STOPPED: abnormal_count,
                Device.STATUS_ALARM: 0,
                Device.STATUS_OFFLINE: 0,
            },
            "generated_at": now,
            "source_updated_at": now,
            "last_success_at": now,
        },
    )


def _test_data_source_connectivity(source: DataSourceConfig) -> bool:
    source_type = (source.source_type or "").strip()
    connection_config = source.connection_config or {}
    if source_type == "opcua":
        return test_opcua_connection(connection_config, node=source.node).ok
    if source_type in {"database", "energy_db", "schedule_db", "wms"}:
        return test_database_connection(connection_config).ok
    # Other source types keep compatibility with existing "mock pass" policy.
    return True


def _filter_line_summaries_by_area(line_summaries: list[dict], area) -> list[dict]:
    filtered = [item for item in line_summaries if (item.get("areaName") or "") == area.name]
    return filtered


def _filter_line_schedules_by_area(line_schedules: list[dict], area) -> list[dict]:
    filtered = [item for item in line_schedules if (item.get("areaName") or "") == area.name]
    return filtered


def _build_risk_counts(line_schedules: list[dict]) -> dict:
    risk_counts = {"normal": 0, "warning": 0, "delayed": 0, "paused": 0}
    for line in line_schedules:
        for order in line.get("orders", []):
            risk_status = order.get("riskStatus")
            if risk_status in risk_counts:
                risk_counts[risk_status] += 1
    return risk_counts


def _filter_area_energy_summaries_by_area(area_summaries: list[dict], area) -> list[dict]:
    return [item for item in area_summaries if (item.get("areaCode") or "") == area.code]


def _sum_energy_consumption(area_summaries: list[dict]) -> str:
    total = Decimal("0")
    for item in area_summaries:
        try:
            total += Decimal(str(item.get("consumption") or "0"))
        except Exception:
            continue
    return str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    value = Decimal(numerator) * Decimal("100.00") / Decimal(denominator)
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _to_positive_decimal(value, fallback: Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception:
        return fallback
    return parsed if parsed > 0 else fallback


def _to_positive_int(value, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _max_iso_datetime(values) -> str | None:
    filtered_values = [value for value in values if value is not None]
    if not filtered_values:
        return None
    return max(filtered_values).isoformat()


def _coalesce_display_text(value: str | None, fallback: str) -> str:
    if value is None:
        return fallback

    normalized = value.strip()
    if not normalized:
        return fallback

    if set(normalized) == {"?"}:
        return fallback

    return normalized


def _build_device_status_items(status_breakdown: dict) -> list[dict]:
    items = []
    for key, display in DEVICE_STATUS_DISPLAY.items():
        items.append(
            {
                "key": key,
                "label": display["label"],
                "accent": display["accent"],
                "count": status_breakdown.get(key, 0),
                "countLabel": f"{status_breakdown.get(key, 0)}",
            }
        )
    return items


def _build_risk_summary_items(risk_counts: dict) -> list[dict]:
    items = []
    for key, display in RISK_STATUS_DISPLAY.items():
        items.append(
            {
                "key": key,
                "label": display["label"],
                "accent": display["accent"],
                "color": display["color"],
                "count": risk_counts.get(key, 0),
                "countLabel": f"{risk_counts.get(key, 0)}",
            }
        )
    return items


def _resolve_mock_risk_status(line_number: int, order_number: int) -> str:
    if line_number % 6 == 0 and order_number == 1:
        return "paused"
    if (line_number + order_number) % 5 == 0:
        return "delayed"
    if (line_number + order_number) % 2 == 0:
        return "warning"
    return "normal"


def _build_production_overview_display(total_target_quantity: int, total_produced_quantity: int, overall_completion_rate) -> dict:
    return {
        "overallCompletionRateLabel": f"{overall_completion_rate}%",
        "totalTargetQuantityLabel": f"{total_target_quantity}",
        "totalProducedQuantityLabel": f"{total_produced_quantity}",
    }


def _build_energy_overview_display(total_consumption, unit: str) -> dict:
    return {
        "totalConsumptionLabel": f"{total_consumption} {unit}",
    }


def _build_energy_area_display(consumption: str, unit: str) -> dict:
    return {
        "consumptionLabel": f"{consumption} {unit}",
    }


def _format_display_datetime(value) -> str:
    if not value:
        return "-"
    if isinstance(value, str):
        value = parse_datetime(value)
    if not value:
        return "-"
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")


def _build_payload_meta_display(last_success_at) -> dict:
    return {
        "lastSuccessfulAtLabel": _format_display_datetime(last_success_at),
    }


def _build_device_overview_display(total_count: int, running_count: int, abnormal_count: int, source_updated_at) -> dict:
    return {
        "sourceUpdatedAtLabel": _format_display_datetime(source_updated_at),
        "totalCountLabel": f"{total_count}",
        "runningCountLabel": f"{running_count}",
        "abnormalCountLabel": f"{abnormal_count}",
    }


def _build_schedule_display(window_days: int) -> dict:
    return {
        "windowDaysLabel": f"{window_days} 天",
    }


def _build_schedule_order_display(risk_status: str, display_start_at: str, display_end_at: str, completion_rate) -> dict:
    risk_display = RISK_STATUS_DISPLAY.get(risk_status, RISK_STATUS_DISPLAY["paused"])
    return {
        "riskLabel": risk_display["label"],
        "riskAccent": risk_display["accent"],
        "timeRangeLabel": f"{display_start_at} - {display_end_at}",
        "completionRateLabel": f"{completion_rate}%",
    }


def _build_production_line_display(
    current_order_code: str,
    target_quantity: int,
    produced_quantity: int,
    completion_rate,
    planned_start_at,
    planned_end_at,
    estimated_completion_at,
    is_delayed: bool,
) -> dict:
    return {
        "currentOrderLabel": f"当前订单 {current_order_code}",
        "targetQuantityLabel": f"目标 {target_quantity}",
        "producedQuantityLabel": f"已产 {produced_quantity}",
        "completionRateLabel": f"{completion_rate}%",
        "plannedRangeLabel": f"{_format_display_datetime(planned_start_at)} - {_format_display_datetime(planned_end_at)}",
        "estimatedCompletionLabel": _format_display_datetime(estimated_completion_at),
        "progressAccent": "red" if is_delayed else "blue",
    }


def _build_production_trend_display(hour_label: str, produced_quantity: int) -> dict:
    return {
        "timeLabel": hour_label,
        "producedQuantityLabel": f"{produced_quantity}",
    }


class _FallbackArea:
    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name


class _FallbackLine:
    def __init__(self, code: str, name: str, area_name: str):
        self.code = code
        self.name = name
        self.area_name = area_name
