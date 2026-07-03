"""销轴产线设备实时监控 — 按车间平面图的工位顺序排列。"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import DataSourceConfig

# 工位定义（key 全局唯一）
_STATION_DEFS: dict[str, dict] = {
    "robot": {"key": "robot", "role": "robot", "label_fmt": "{line}号线"},
    "lathe_5": {"key": "lathe_5", "role": "lathe", "label": "车床5", "device_keywords": ("车床5",)},
    "lathe_4": {"key": "lathe_4", "role": "lathe", "label": "车床4", "device_keywords": ("车床4",)},
    "lathe_3": {"key": "lathe_3", "role": "lathe", "label": "车床3", "device_keywords": ("车床3",)},
    "lathe_2": {"key": "lathe_2", "role": "lathe", "label": "车床2", "device_keywords": ("车床2",)},
    "lathe_1": {"key": "lathe_1", "role": "lathe", "label": "车床1", "device_keywords": ("车床1",)},
    "dual_spindle_1": {
        "key": "dual_spindle_1",
        "role": "dual_spindle",
        "label": "双主轴1",
        "device_keywords": ("双主轴1", "双主轴"),
    },
}

# 5 号线（及默认）：机器手 → 车床5~1 → 双主轴1
_DEFAULT_LINE_STATION_KEYS: tuple[str, ...] = (
    "robot",
    "lathe_5",
    "lathe_4",
    "lathe_3",
    "lathe_2",
    "lathe_1",
    "dual_spindle_1",
)

# 各产线实际工位（与现场布置一致；未列出的产线沿用默认 7 工位）
XIAOZHOU_LINE_LAYOUTS: dict[int, tuple[str, ...]] = {
    # 1 号线无车床4、车床5
    1: ("robot", "lathe_3", "lathe_2", "lathe_1", "dual_spindle_1"),
    2: _DEFAULT_LINE_STATION_KEYS,
    3: _DEFAULT_LINE_STATION_KEYS,
    4: _DEFAULT_LINE_STATION_KEYS,
    5: _DEFAULT_LINE_STATION_KEYS,
}

# 兼容旧引用：默认产线工位顺序
XIAOZHOU_LINE_STATION_TEMPLATE: tuple[dict, ...] = tuple(
    _STATION_DEFS[key] for key in _DEFAULT_LINE_STATION_KEYS
)


def line_station_template(line_number: int) -> tuple[dict, ...]:
    keys = XIAOZHOU_LINE_LAYOUTS.get(line_number, _DEFAULT_LINE_STATION_KEYS)
    return tuple(_STATION_DEFS[key] for key in keys)


def _line_number_in_text(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d)\s*号线", text)
    if match:
        return int(match.group(1))
    match = re.search(r"LINE-(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"LINE(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def infer_line_number_from_source(source: "DataSourceConfig") -> int | None:
    code = (source.code or "").upper()
    match = re.search(r"LINE(\d+)", code)
    if match:
        return int(match.group(1))
    for text in (source.name or "", source.code or ""):
        inferred = _line_number_in_text(text)
        if inferred is not None:
            return inferred
    for device in source.devices.all():
        for text in (device.name or "", device.code or ""):
            inferred = _line_number_in_text(text)
            if inferred is not None:
                return inferred
    return None


def station_label(line_number: int, station_def: dict) -> str:
    label_fmt = station_def.get("label_fmt")
    if label_fmt:
        return label_fmt.format(line=line_number)
    return station_def.get("label") or station_def["key"]


def match_s7_source_to_line_robot(source: "DataSourceConfig", line_number: int) -> bool:
    if (source.source_type or "").strip() != "s7":
        return False
    inferred = infer_line_number_from_source(source)
    return inferred == line_number


def _text_belongs_to_line(text: str, line_number: int) -> bool:
    inferred = _line_number_in_text(text)
    if inferred is not None:
        return inferred == line_number
    return False


def _keyword_matches_station(text: str, keyword: str) -> bool:
    """避免「车床1」误匹配「车床10」。"""
    if not keyword or keyword not in text:
        return False
    start = 0
    while True:
        idx = text.find(keyword, start)
        if idx < 0:
            return False
        after = text[idx + len(keyword) : idx + len(keyword) + 1]
        if not after or not after.isdigit():
            return True
        start = idx + 1


def _text_matches_station(text: str, station_def: dict) -> bool:
    label = station_def.get("label") or ""
    if label and _keyword_matches_station(text, label):
        return True
    for keyword in station_def.get("device_keywords") or ():
        if _keyword_matches_station(text, keyword):
            return True
    return False


def match_opcua_source_to_station(
    source: "DataSourceConfig",
    station_def: dict,
    line_number: int,
    area,
) -> bool:
    if station_def.get("role") == "robot":
        return False

    inferred = infer_line_number_from_source(source)
    if inferred is not None and inferred != line_number:
        return False

    haystacks: list[str] = [source.name or "", source.code or ""]
    for device in source.devices.filter(area=area, is_active=True):
        haystacks.append(device.name or "")
        haystacks.append(device.code or "")

    for text in haystacks:
        if not _text_belongs_to_line(text, line_number):
            continue
        if _text_matches_station(text, station_def):
            return True
    return False
