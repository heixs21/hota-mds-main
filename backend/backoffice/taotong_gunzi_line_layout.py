"""套筒滚子设备实时监控 — 9 行 × 3 列车间布置（行内左→右：车床3、车床2、车床1）。"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .taotong_gunzi_device_seed import TAOTONG_GUNZI_LINES, _device_code, iter_taotong_gunzi_devices

if TYPE_CHECKING:
    from .models import DataSourceConfig

GRID_COLUMNS = 3

# 屏幕列位 → 车床编号（与 IP 布置图一致：右侧为车床1）
_LINE_GRID_LATHE_BY_COLUMN: dict[int, tuple[int | None, ...]] = {
    1: (3, 2, 1),
    2: (3, 2, 1),
    3: (3, 2, 1),
    4: (3, 2, 1),
    5: (3, 2, 1),
    6: (3, 2, 1),
    7: (3, 2, 1),
    8: (None, 2, 1),
    9: (None, 2, 1),
}


def taotong_line_numbers() -> tuple[int, ...]:
    return tuple(line["line_number"] for line in TAOTONG_GUNZI_LINES)


def taotong_line_label(line_number: int) -> str:
    return f"套筒滚子{line_number}号线"


def taotong_lathe_label(line_number: int, lathe_index: int) -> str:
    return f"{taotong_line_label(line_number)}车床{lathe_index}"


def taotong_line_grid_stations(line_number: int) -> tuple[dict, ...]:
    """返回一行 3 个列位（含空位）。"""
    mapping = _LINE_GRID_LATHE_BY_COLUMN.get(line_number, (3, 2, 1))
    line_code = next(item["line_code"] for item in TAOTONG_GUNZI_LINES if item["line_number"] == line_number)
    stations: list[dict] = []
    for col_index, lathe_index in enumerate(mapping, start=1):
        if lathe_index is None:
            stations.append(
                {
                    "column": col_index,
                    "stationKey": f"empty-{col_index}",
                    "latheIndex": None,
                    "empty": True,
                    "label": "",
                    "deviceCode": "",
                }
            )
            continue
        stations.append(
            {
                "column": col_index,
                "stationKey": f"lathe_{lathe_index}",
                "latheIndex": lathe_index,
                "empty": False,
                "label": taotong_lathe_label(line_number, lathe_index),
                "deviceCode": _device_code(line_code, lathe_index),
            }
        )
    return tuple(stations)


def _line_number_from_source(source: "DataSourceConfig") -> int | None:
    code = (source.code or "").upper()
    match = re.search(r"DS-02(\d{3})", code)
    if match:
        seq = int(match.group(1))
        devices = list(iter_taotong_gunzi_devices())
        if 1 <= seq <= len(devices):
            line_code = devices[seq - 1]["line_code"]
            return int(line_code.rsplit("-", 1)[-1].replace("L", ""))
    for device in source.devices.all():
        match = re.search(r"TTGZ-L(\d{2})", device.code or "")
        if match:
            return int(match.group(1))
    name = source.name or ""
    match = re.search(r"套筒滚子(\d+)号线", name)
    if match:
        return int(match.group(1))
    return None


def _lathe_index_from_source(source: "DataSourceConfig", line_number: int) -> int | None:
    line_code = f"TTGZ-L{line_number:02d}"
    for device in source.devices.all():
        match = re.search(rf"{re.escape(line_code)}-LT(\d{{2}})", device.code or "")
        if match:
            return int(match.group(1))
    name = source.name or ""
    match = re.search(rf"套筒滚子{line_number}号线车床(\d+)", name)
    if match:
        return int(match.group(1))
    code = (source.code or "").upper()
    match = re.search(r"DS-02(\d{3})", code)
    if match:
        seq = int(match.group(1))
        devices = list(iter_taotong_gunzi_devices())
        if 1 <= seq <= len(devices):
            item = devices[seq - 1]
            if int(item["line_code"].rsplit("-", 1)[-1].replace("L", "")) == line_number:
                return int(item["device_code"].rsplit("-LT", 1)[-1])
    return None


def match_opcua_source_to_taotong_station(
    source: "DataSourceConfig",
    line_number: int,
    lathe_index: int,
) -> bool:
    if _lathe_index_from_source(source, line_number) == lathe_index:
        return True
    expected_code = _device_code(f"TTGZ-L{line_number:02d}", lathe_index)
    return source.devices.filter(code=expected_code, is_active=True).exists()
