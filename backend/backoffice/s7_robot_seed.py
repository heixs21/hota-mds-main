"""销轴产线机器手 S7 点位定义（222.md）。"""

from __future__ import annotations

DB_NUMBER = 79

# 每条线：数据源编码、名称、PLC、DB79 区段起始字节、代表设备编码/名称
XIAOZHOU_S7_ROBOT_LINES: tuple[dict, ...] = (
    {
        "line": 1,
        "source_code": "DS-S7-LINE1",
        "source_name": "销轴1号线机器手",
        "host": "192.168.31.49",
        "rack": 0,
        "slot": 1,
        "base_offset": 0,
        "device_code": "XZ-S7-ROBOT-1",
        "device_name": "销轴1号线机器手",
    },
    {
        "line": 2,
        "source_code": "DS-S7-LINE2",
        "source_name": "销轴2号线机器手",
        "host": "192.168.31.2",
        "rack": 0,
        "slot": 1,
        "base_offset": 48,
        "device_code": "XZ-S7-ROBOT-2",
        "device_name": "销轴2号线机器手",
    },
    {
        "line": 3,
        "source_code": "DS-S7-LINE3",
        "source_name": "销轴3号线机器手",
        "host": "192.168.31.2",
        "rack": 0,
        "slot": 1,
        "base_offset": 32,
        "device_code": "XZ-S7-ROBOT-3",
        "device_name": "销轴3号线机器手",
    },
    {
        "line": 4,
        "source_code": "DS-S7-LINE4",
        "source_name": "销轴4号线机器手",
        "host": "192.168.31.2",
        "rack": 0,
        "slot": 1,
        "base_offset": 0,
        "device_code": "XZ-S7-ROBOT-4",
        "device_name": "销轴4号线机器手",
    },
    {
        "line": 5,
        "source_code": "DS-S7-LINE5",
        "source_name": "销轴5号线机器手",
        "host": "192.168.31.2",
        "rack": 0,
        "slot": 1,
        "base_offset": 16,
        "device_code": "XZ-S7-ROBOT-5",
        "device_name": "销轴5号线机器手",
    },
)


def build_s7_robot_line_nodes(line: int, base_offset: int) -> list[dict]:
    """按 222.md 生成单条产线在 DB79 内的 6 个点位。"""
    prefix = f"{line}线"
    base = int(base_offset)
    return [
        {
            "dbNumber": DB_NUMBER,
            "offset": base,
            "bit": 0,
            "dataType": "bool",
            "comment": f"{prefix}运行",
        },
        {
            "dbNumber": DB_NUMBER,
            "offset": base,
            "bit": 1,
            "dataType": "bool",
            "comment": f"{prefix}停止",
        },
        {
            "dbNumber": DB_NUMBER,
            "offset": base,
            "bit": 2,
            "dataType": "bool",
            "comment": f"{prefix}故障",
        },
        {
            "dbNumber": DB_NUMBER,
            "offset": base + 2,
            "dataType": "int",
            "comment": f"{prefix}东北筐生产计数",
        },
        {
            "dbNumber": DB_NUMBER,
            "offset": base + 4,
            "dataType": "int",
            "comment": f"{prefix}西南筐生产计数",
        },
        {
            "dbNumber": DB_NUMBER,
            "offset": base + 6,
            "length": 10,
            "dataType": "string",
            "comment": f"{prefix}物料编码",
        },
    ]


def s7_robot_line_seed_payload(line_def: dict, *, refresh_interval_seconds: int = 30) -> dict:
    line = int(line_def["line"])
    base_offset = int(line_def["base_offset"])
    return {
        "code": line_def["source_code"],
        "name": line_def["source_name"],
        "source_type": "s7",
        "is_enabled": True,
        "refresh_interval_seconds": refresh_interval_seconds,
        "connection_config": {
            "host": line_def["host"],
            "rack": line_def["rack"],
            "slot": line_def["slot"],
        },
        "node": build_s7_robot_line_nodes(line, base_offset),
        "notes": f"222.md 销轴{line}号线机器手 DB{DB_NUMBER}；seed_xiaozhou_s7_robot_lines 生成",
    }
