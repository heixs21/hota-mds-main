"""套筒滚子机床设备台账 — 1~9 号线同一区域，每行一条产线，行内自右向左为车床1起。"""

from __future__ import annotations

IP_PREFIX = "192.168"

TAOTONG_GUNZI_AREA = {
    "code": "TTGZ",
    "name": "套筒滚子",
}

# 自上而下：1~9 号线（末两线各 2 台）
TAOTONG_GUNZI_LINES: tuple[dict, ...] = (
    {
        "line_number": 1,
        "line_code": "TTGZ-L01",
        "line_name": "套筒滚子1号线",
        "lathe_ips": ("31.65", "31.66", "31.67"),
    },
    {
        "line_number": 2,
        "line_code": "TTGZ-L02",
        "line_name": "套筒滚子2号线",
        "lathe_ips": ("31.68", "31.69", "31.70"),
    },
    {
        "line_number": 3,
        "line_code": "TTGZ-L03",
        "line_name": "套筒滚子3号线",
        "lathe_ips": ("31.71", "31.72", "31.73"),
    },
    {
        "line_number": 4,
        "line_code": "TTGZ-L04",
        "line_name": "套筒滚子4号线",
        "lathe_ips": ("35.76", "35.77", "35.78"),
    },
    {
        "line_number": 5,
        "line_code": "TTGZ-L05",
        "line_name": "套筒滚子5号线",
        "lathe_ips": ("35.79", "35.80", "35.81"),
    },
    {
        "line_number": 6,
        "line_code": "TTGZ-L06",
        "line_name": "套筒滚子6号线",
        "lathe_ips": ("35.82", "35.83", "35.84"),
    },
    {
        "line_number": 7,
        "line_code": "TTGZ-L07",
        "line_name": "套筒滚子7号线",
        "lathe_ips": ("35.85", "35.86", "35.87"),
    },
    {
        "line_number": 8,
        "line_code": "TTGZ-L08",
        "line_name": "套筒滚子8号线",
        "lathe_ips": ("35.88", "35.89"),
    },
    {
        "line_number": 9,
        "line_code": "TTGZ-L09",
        "line_name": "套筒滚子9号线",
        "lathe_ips": ("35.90", "35.91"),
    },
)

# 旧版 seed 遗留编码（分区域 TTGZ-2F），再次执行时清理
LEGACY_DEVICE_CODE_PREFIXES = ("TTGZ-2F-",)
LEGACY_LINE_CODE_PREFIXES = ("TTGZ-2F-",)
LEGACY_AREA_CODES = ("TTGZ-2F",)


def _full_ip(ip_suffix: str) -> str:
    return f"{IP_PREFIX}.{ip_suffix}"


def _device_code(line_code: str, lathe_index: int) -> str:
    return f"{line_code}-LT{lathe_index:02d}"


def iter_taotong_gunzi_devices() -> list[dict]:
    """展开为设备台账写入条目。"""
    out: list[dict] = []
    area_code = TAOTONG_GUNZI_AREA["code"]
    for line_def in TAOTONG_GUNZI_LINES:
        line_no = line_def["line_number"]
        line_code = line_def["line_code"]
        name_prefix = f"套筒滚子{line_no}号线"
        for index, ip_suffix in enumerate(line_def["lathe_ips"], start=1):
            out.append(
                {
                    "area_code": area_code,
                    "area_name": TAOTONG_GUNZI_AREA["name"],
                    "line_code": line_code,
                    "line_name": line_def["line_name"],
                    "device_code": _device_code(line_code, index),
                    "device_name": f"{name_prefix}车床{index}",
                    "ip": _full_ip(ip_suffix),
                }
            )
    return out
