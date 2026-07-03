"""设备实时监控 — 展示模式演示数据（全部在线、跳过现场连接）。"""

from __future__ import annotations

from django.utils import timezone

from .realtime_dashboard_services import (
    REALTIME_LAYOUT_SYNTEC_CNC,
    REALTIME_LAYOUT_TAOTONG_GUNZI_LINE,
    REALTIME_LAYOUT_XIAOZHOU_LINE,
    build_syntec_cnc_dashboard_view,
)
from .taotong_gunzi_line_layout import taotong_line_grid_stations, taotong_line_label, taotong_line_numbers
from .xiaozhou_line_layout import line_station_template, station_label


def _demo_seed(line_number: int, station_key: str) -> int:
    return line_number * 17 + sum(ord(c) for c in station_key)


def _demo_syntec_vm(seed: int) -> dict[str, tuple[bool, object]]:
    rpm = 2600 + (seed % 7) * 180
    load = 35 + (seed % 11) * 3
    parts = 120 + seed * 3
    tool = 1 + (seed % 8)
    line_no = 100 + seed * 5
    return {
        "CNCInterface/CncChannelList0/CncChannel1/ActProgramStatus0": (True, "1"),
        "CNCInterface/CncChannelList0/CncChannel1/ActOperationMode0": (True, "AUTO"),
        "CNCInterface/CncChannelList0/CncChannel1/FeedHold0": (True, "0"),
        "CNCInterface/CncChannelList0/CncChannel1/ActProgramName0": (True, f"O{1000 + seed}.NC"),
        "CNCInterface/CncChannelList0/CncChannel1/ActMainProgramLine0": (True, str(line_no)),
        "CNCInterface/CncChannelList0/CncChannel1/TotalPartCount0": (True, str(parts)),
        "CNCInterface/CncChannelList0/CncChannel1/ToolId0": (True, str(tool)),
        "CNCInterface/CncChannelList0/CncChannel1/ActFeedrate0": (True, "100"),
        "CNCInterface/CncChannelList0/CncChannel1/CmdOverride0": (True, "100"),
        "CNCInterface/CncSpindleList0/CncSpindle1/ActSpeed0": (True, str(rpm)),
        "CNCInterface/CncSpindleList0/CncSpindle1/ActLoad0": (True, str(load)),
        "CNCInterface/CncSpindleList0/CncSpindle1/ActOverride0": (True, "100"),
        "CNCInterface/PowerOnSpan0": (True, str(7200 + seed * 120)),
    }


def build_demo_s7_robot_card(line_number: int) -> dict:
    base_ts = timezone.localtime().isoformat()
    display_title = f"{line_number}号线"
    seed = _demo_seed(line_number, "robot")
    ne_count = str(10 + seed % 15)
    sw_count = str(20 + seed % 20)
    material = f"XZ{line_number:02d}{1000 + seed % 9000:04d}"
    prefix = f"{line_number}线"
    robot_items = [
        {"comment": f"{prefix}运行", "value": "True", "ok": True, "error": ""},
        {"comment": f"{prefix}停止", "value": "False", "ok": True, "error": ""},
        {"comment": f"{prefix}故障", "value": "False", "ok": True, "error": ""},
        {"comment": f"{prefix}东北筐生产计数", "value": ne_count, "ok": True, "error": ""},
        {"comment": f"{prefix}西南筐生产计数", "value": sw_count, "ok": True, "error": ""},
        {"comment": f"{prefix}物料编码", "value": material, "ok": True, "error": ""},
    ]
    return {
        "sourceCode": f"DEMO-S7-LINE{line_number}",
        "sourceName": f"{display_title}机器手",
        "deviceName": display_title,
        "displayTitle": display_title,
        "subtitle": "机器手",
        "mergeLayout": False,
        "dashboardTemplate": "s7_robot",
        "status": "online",
        "offlineReason": "",
        "updatedAt": base_ts,
        "machineStatus": {
            "label": "运行",
            "indicator": "green",
            "borderColor": "green",
            "alarmActive": False,
        },
        "robot": {
            "displayTitle": display_title,
            "status": "online",
            "items": robot_items,
        },
        "s7Extras": {
            "neCount": ne_count,
            "swCount": sw_count,
            "materialCode": material,
        },
        "parameters": robot_items,
        "groupedParameters": [],
    }


def build_demo_syntec_cnc_station_card(line_number: int, station_def: dict) -> dict:
    base_ts = timezone.localtime().isoformat()
    label = station_label(line_number, station_def)
    seed = _demo_seed(line_number, station_def["key"])
    vm = _demo_syntec_vm(seed)
    dash = build_syntec_cnc_dashboard_view(vm, offline=False, device_model_fallback="新代 CNC")
    return {
        "sourceCode": f"DEMO-{line_number}-{station_def['key']}",
        "sourceName": label,
        "deviceName": label,
        "displayTitle": label,
        "subtitle": "",
        "mergeLayout": False,
        "dashboardTemplate": REALTIME_LAYOUT_SYNTEC_CNC,
        "status": "online",
        "offlineReason": "",
        "updatedAt": base_ts,
        "parameters": [],
        "groupedParameters": [],
        **dash,
    }


def build_xiaozhou_line_demo_monitor(*, poll_interval_seconds: int) -> dict:
    lines_out: list[dict] = []
    for line_number in range(1, 6):
        stations_out: list[dict] = []
        for station_def in line_station_template(line_number):
            label = station_label(line_number, station_def)
            if station_def["role"] == "robot":
                card = build_demo_s7_robot_card(line_number)
            else:
                card = build_demo_syntec_cnc_station_card(line_number, station_def)
                card["dashboardTemplate"] = "syntec_cnc_compact"
            stations_out.append(
                {
                    "stationKey": station_def["key"],
                    "role": station_def["role"],
                    "label": label,
                    "pending": False,
                    "card": card,
                }
            )
        lines_out.append(
            {
                "lineNumber": line_number,
                "lineLabel": f"{line_number}号线",
                "stations": stations_out,
            }
        )

    return {
        "realtimeLayout": REALTIME_LAYOUT_XIAOZHOU_LINE,
        "pollIntervalSeconds": poll_interval_seconds,
        "demoMode": True,
        "lines": lines_out,
        "cards": [],
    }


def build_taotong_gunzi_line_demo_monitor(*, poll_interval_seconds: int) -> dict:
    lines_out: list[dict] = []
    for line_number in taotong_line_numbers():
        stations_out: list[dict] = []
        for station_def in taotong_line_grid_stations(line_number):
            if station_def.get("empty"):
                stations_out.append(
                    {
                        "stationKey": station_def["stationKey"],
                        "column": station_def["column"],
                        "label": "",
                        "empty": True,
                        "pending": False,
                        "card": {
                            "sourceCode": f"demo-empty-{line_number}-{station_def['stationKey']}",
                            "dashboardTemplate": "empty_slot",
                            "status": "empty",
                        },
                    }
                )
                continue
            label = station_def["label"]
            card = build_demo_syntec_cnc_station_card(
                line_number,
                {"key": station_def["stationKey"], "label": f"车床{station_def['latheIndex']}"},
            )
            card["dashboardTemplate"] = "syntec_cnc_compact"
            card["displayTitle"] = label
            card["deviceName"] = label
            card["sourceName"] = label
            stations_out.append(
                {
                    "stationKey": station_def["stationKey"],
                    "column": station_def["column"],
                    "label": label,
                    "empty": False,
                    "pending": False,
                    "card": card,
                }
            )
        lines_out.append(
            {
                "lineNumber": line_number,
                "lineLabel": taotong_line_label(line_number),
                "stations": stations_out,
            }
        )

    return {
        "realtimeLayout": REALTIME_LAYOUT_TAOTONG_GUNZI_LINE,
        "pollIntervalSeconds": poll_interval_seconds,
        "demoMode": True,
        "lines": lines_out,
        "cards": [],
    }


def build_generic_realtime_demo_monitor(*, layout: str | None, poll_interval_seconds: int) -> dict:
    cards = []
    demo_stations = [
        ("lathe_1", "车床1"),
        ("lathe_2", "车床2"),
        ("lathe_3", "车床3"),
        ("dual_spindle_1", "双主轴1"),
    ]
    for index, (key, title) in enumerate(demo_stations, start=1):
        station_def = {"key": key, "label": title}
        card = build_demo_syntec_cnc_station_card(index, station_def)
        card["displayTitle"] = title
        card["deviceName"] = title
        card["sourceName"] = title
        cards.append(card)

    return {
        "realtimeLayout": (layout or "").strip() or REALTIME_LAYOUT_SYNTEC_CNC,
        "pollIntervalSeconds": poll_interval_seconds,
        "demoMode": True,
        "lines": [],
        "cards": cards,
    }
