"""设备实时监控仪表盘：按区域/数据源模板拆分渲染结构。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import DataSourceConfig

REALTIME_LAYOUT_AUTO = ""
REALTIME_LAYOUT_SIEMENS_BORING = "siemens_boring"
REALTIME_LAYOUT_SYNTEC_CNC = "syntec_cnc"
REALTIME_LAYOUT_PARAMETER_GRID = "parameter_grid"
REALTIME_LAYOUT_XIAOZHOU_LINE = "xiaozhou_line"
REALTIME_LAYOUT_TAOTONG_GUNZI_LINE = "taotong_gunzi_line"

REALTIME_LAYOUT_CHOICES = (
    (REALTIME_LAYOUT_AUTO, "自动识别"),
    (REALTIME_LAYOUT_SIEMENS_BORING, "西门子镗孔"),
    (REALTIME_LAYOUT_SYNTEC_CNC, "新代 CNC"),
    (REALTIME_LAYOUT_PARAMETER_GRID, "参数列表"),
    (REALTIME_LAYOUT_XIAOZHOU_LINE, "销轴产线布局"),
    (REALTIME_LAYOUT_TAOTONG_GUNZI_LINE, "套筒滚子产线布局"),
)

_SYNTEC_CH = "CNCInterface/CncChannelList0/CncChannel1"
_SYNTEC_SP = "CNCInterface/CncSpindleList0/CncSpindle1"

# 111.md 方案 A — 可直接粘贴后台「节点 ID 列表」
XIAOZHOU_SYNTEC_SCHEME_A_NODES = [
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ActProgramStatus0", "comment": "控制器状态"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ActOperationMode0", "comment": "控制器运行模式"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/FeedHold0", "comment": "加工暂停状态"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/TotalPartCount0", "comment": "加工总工件数"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ToolId0", "comment": "主轴当前刀号"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ActProgramName0", "comment": "当前正在执行的程序名"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ActMainProgramLine0", "comment": "主程序当前执行 N 行号"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/ActFeedrate0", "comment": "系统实际进给倍率"},
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/CmdOverride0", "comment": "进给百分比指令值"},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/ActSpeed0", "comment": "主轴 1 实际转速"},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/ActLoad0", "comment": "主轴 1 负载率"},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/ActOverride0", "comment": "主轴 1 实际转速百分比"},
    {
        "nodeId": "ns=1;s=CNCInterface/CurrentAlarm0",
        "comment": "历史报警列表",
        "subscribe": "on_alarm",
        "readWhen": "alarm",
    },
    {"nodeId": "ns=1;s=CNCInterface/CncChannelList0/CncChannel1/Id0", "comment": "轴群编号", "subscribe": False},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/IsInactive0", "comment": "主轴 1 是否无使能", "subscribe": False},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/IsVirtual0", "comment": "主轴 1 是否为虚拟轴", "subscribe": False},
    {"nodeId": "ns=1;s=CNCInterface/CncSpindleList0/CncSpindle1/ActChannel0", "comment": "主轴 1 驱动器站号", "subscribe": False},
    {"nodeId": "ns=1;s=CNCInterface/PowerOnSpan0", "comment": "控制器开机时间", "subscribe": False},
]


def _parse_numeric_scalar(raw):
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


def _parse_int_scalar(raw):
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
        total = int(float(sec_val))
    except (TypeError, ValueError):
        return "--"
    if total < 0:
        return "--"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _normalize_syntec_percent(raw) -> float | None:
    """新代倍率字段可能是 0–100，也可能是 0–10000（需 /100）。"""
    n = _parse_numeric_scalar(raw)
    if n is None:
        return None
    if n > 200:
        n = n / 100.0
    return min(100.0, max(0.0, n))


def _vm_get(vm: dict[str, tuple[bool, object]], path: str) -> tuple[bool, object]:
    if path in vm:
        return vm[path]
    for key, pair in vm.items():
        if key.endswith(path) or path in key:
            return pair
    return False, None


def normalize_opcua_node_config(source: "DataSourceConfig") -> list[dict]:
    from .connection_test_services import _normalize_opcua_nodes

    return _normalize_opcua_nodes(source.node, source.connection_config or {})


def detect_opcua_realtime_layout(source: "DataSourceConfig") -> str:
    """根据节点 namespace / 路径推断仪表盘模板。"""
    seen_ns1_cnc = False
    seen_ns2 = False
    for cfg in normalize_opcua_node_config(source):
        nid = (cfg.get("nodeId") or "").strip().lower()
        if "cncinterface/" in nid or nid.startswith("ns=1;"):
            seen_ns1_cnc = True
        if "ns=2" in nid and ("/channel/" in nid or nid.startswith("ns=2;s=/")):
            seen_ns2 = True
    if seen_ns1_cnc and not seen_ns2:
        return REALTIME_LAYOUT_SYNTEC_CNC
    if seen_ns2:
        return REALTIME_LAYOUT_SIEMENS_BORING
    return REALTIME_LAYOUT_PARAMETER_GRID


def resolve_realtime_layout(source: "DataSourceConfig", binding_layout: str | None) -> str:
    layout = (binding_layout or REALTIME_LAYOUT_AUTO).strip()
    if layout and layout != REALTIME_LAYOUT_AUTO:
        return layout
    return detect_opcua_realtime_layout(source)


def should_merge_production_line_cards(binding_layout: str | None, sources=None) -> bool:
    """仅西门子镗孔产线（CNC+机器人）做产线合并；新代 CNC 始终单源卡片。"""
    layout = (binding_layout or REALTIME_LAYOUT_AUTO).strip()
    if layout in (REALTIME_LAYOUT_SYNTEC_CNC, REALTIME_LAYOUT_PARAMETER_GRID):
        return False
    if layout == REALTIME_LAYOUT_SIEMENS_BORING:
        return True
    if sources:
        layouts = {detect_opcua_realtime_layout(source) for source in sources}
        return REALTIME_LAYOUT_SIEMENS_BORING in layouts
    return False


_SYNTEC_ALARM_STATUS = frozenset(
    {
        "3",
        "4",
        "alarm",
        "ALARM",
        "Alarm",
        "报警",
        "故障",
        "error",
        "ERROR",
    }
)


def syntec_program_status_is_alarm(status_raw) -> bool:
    key = str(status_raw or "").strip()
    if not key:
        return False
    if key in _SYNTEC_ALARM_STATUS:
        return True
    low = key.lower()
    return any(token in low for token in ("alarm", "报警", "故障", "fault", "error"))


def _resolve_syntec_machine_status(*, offline: bool, status_raw, feed_hold_raw) -> dict:
    if offline:
        return {
            "code": "offline",
            "label": "离线",
            "borderColor": "gray",
            "alarmActive": False,
            "indicator": "gray",
        }
    if syntec_program_status_is_alarm(status_raw):
        return {
            "code": "alarm",
            "label": "报警",
            "borderColor": "red",
            "alarmActive": True,
            "indicator": "red",
        }
    hold = _parse_int_scalar(feed_hold_raw)
    if hold not in (None, 0):
        return {
            "code": "hold",
            "label": "暂停",
            "borderColor": "yellow",
            "alarmActive": False,
            "indicator": "yellow",
        }
    status_key = str(status_raw or "").strip()
    mapping = {
        "0": ("standby", "停止", "yellow"),
        "1": ("running", "加工", "green"),
        "2": ("standby", "闲置", "yellow"),
    }
    code, label, color = mapping.get(status_key, ("standby", "待机", "yellow"))
    return {
        "code": code,
        "label": label,
        "borderColor": color,
        "alarmActive": False,
        "indicator": color,
    }


def fetch_syntec_current_alarm_text(connection_config: dict, alarm_node: dict | None) -> str:
    if not alarm_node:
        return ""
    from .connection_test_services import _read_opcua_nodes_direct

    result = _read_opcua_nodes_direct(connection_config or {}, [alarm_node])
    if not result.items:
        return ""
    item = result.items[0]
    if not item.ok:
        return ""
    return str(item.value or "").strip()


def find_syntec_current_alarm_node(node_config: list[dict]) -> dict | None:
    for item in node_config:
        node_id = (item.get("nodeId") or "").strip()
        if "CurrentAlarm0" in node_id:
            return item
    return None


def build_syntec_cnc_dashboard_view(
    vm: dict[str, tuple[bool, object]],
    *,
    offline: bool,
    device_model_fallback: str = "新代 CNC",
    alarm_text: str = "",
) -> dict:
    ok_status, status_raw = _vm_get(vm, f"{_SYNTEC_CH}/ActProgramStatus0")
    ok_mode, mode_raw = _vm_get(vm, f"{_SYNTEC_CH}/ActOperationMode0")
    ok_hold, hold_raw = _vm_get(vm, f"{_SYNTEC_CH}/FeedHold0")

    ms = _resolve_syntec_machine_status(
        offline=offline,
        status_raw=status_raw if ok_status else None,
        feed_hold_raw=hold_raw if ok_hold else None,
    )

    ok_spd, act_speed = _vm_get(vm, f"{_SYNTEC_SP}/ActSpeed0")
    ok_load, act_load = _vm_get(vm, f"{_SYNTEC_SP}/ActOverride0")
    ok_sp_load, sp_load = _vm_get(vm, f"{_SYNTEC_SP}/ActLoad0")

    spindle_slot = {
        "label": "主轴",
        "configured": not offline,
        "actSpeedRpm": _parse_numeric_scalar(act_speed) if ok_spd else None,
        "cmdSpeedRpm": None,
        "speedOverridePct": _normalize_syntec_percent(act_load) if ok_load else None,
        "temperatureC": None,
        "loadPct": _parse_numeric_scalar(sp_load) if ok_sp_load else None,
    }

    ok_prog, prog_name = _vm_get(vm, f"{_SYNTEC_CH}/ActProgramName0")
    ok_line, exe_line = _vm_get(vm, f"{_SYNTEC_CH}/ActMainProgramLine0")
    ok_parts, part_count = _vm_get(vm, f"{_SYNTEC_CH}/TotalPartCount0")
    ok_tool, tool_id = _vm_get(vm, f"{_SYNTEC_CH}/ToolId0")
    ok_feed, feed_rate = _vm_get(vm, f"{_SYNTEC_CH}/ActFeedrate0")
    ok_cmd_ovr, cmd_override = _vm_get(vm, f"{_SYNTEC_CH}/CmdOverride0")
    ok_power, power_span = _vm_get(vm, "CNCInterface/PowerOnSpan0")

    mode_label = "--"
    if not offline and ok_mode and str(mode_raw or "").strip():
        mode_label = str(mode_raw).strip()

    return {
        "deviceModel": device_model_fallback or "新代 CNC",
        "machineStatus": {
            **ms,
            "programStatus": str(status_raw).strip() if ok_status and status_raw is not None else None,
            "alarmText": alarm_text if ms.get("code") == "alarm" and alarm_text else "",
        },
        "spindles": [spindle_slot],
        "job": {
            "mainProgram": "--" if offline else (str(prog_name).strip() if ok_prog and str(prog_name or "").strip() else "--"),
            "exeLine": "--" if offline else (str(exe_line).strip() if ok_line and str(exe_line or "").strip() else "--"),
            "cycleTimeFormatted": "--",
            "operationTimeFormatted": "--" if offline else _format_seconds_hms(power_span if ok_power else None),
            "workModeTag": mode_label,
        },
        "syntecExtras": {
            "totalPartCount": _parse_int_scalar(part_count) if ok_parts else None,
            "toolId": _parse_int_scalar(tool_id) if ok_tool else None,
            "feedOverridePct": _normalize_syntec_percent(feed_rate) if ok_feed else None,
            "cmdOverridePct": _normalize_syntec_percent(cmd_override) if ok_cmd_ovr else None,
            "currentAlarm": alarm_text if ms.get("code") == "alarm" and alarm_text else "",
        },
    }


def build_parameter_grid_dashboard_view(*, offline: bool) -> dict:
    """仅展示参数列表，不使用 CNC 仪表盘结构。"""
    ms = {
        "code": "offline" if offline else "online",
        "label": "离线" if offline else "在线",
        "borderColor": "gray" if offline else "green",
        "alarmActive": False,
        "indicator": "gray" if offline else "green",
    }
    return {
        "deviceModel": "--",
        "machineStatus": ms,
        "spindles": [],
        "job": {
            "mainProgram": "--",
            "exeLine": "--",
            "cycleTimeFormatted": "--",
            "operationTimeFormatted": "--",
            "workModeTag": "--",
        },
    }
