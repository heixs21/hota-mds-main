"""套筒滚子 OPC UA 数据源 — 每台车床一个源，节点列表与销轴新代方案 A 相同。"""

from __future__ import annotations

from backoffice.realtime_dashboard_services import XIAOZHOU_SYNTEC_SCHEME_A_NODES
from backoffice.taotong_gunzi_device_seed import iter_taotong_gunzi_devices

OPCUA_SOURCE_CODE_START = 2001
DEFAULT_OPCUA_PORT = 4840


def _source_code(sequence: int) -> str:
    return f"DS-{OPCUA_SOURCE_CODE_START + sequence - 1:05d}"


def opcua_endpoint_url(ip: str, *, port: int = DEFAULT_OPCUA_PORT) -> str:
    return f"opc.tcp://{ip}:{port}"


def iter_taotong_gunzi_opcua_sources(*, port: int = DEFAULT_OPCUA_PORT) -> list[dict]:
    """按设备台账顺序展开 OPC UA 数据源（DS-02001 起）。"""
    out: list[dict] = []
    for sequence, device in enumerate(iter_taotong_gunzi_devices(), start=1):
        out.append(
            {
                "source_code": _source_code(sequence),
                "source_name": device["device_name"],
                "device_code": device["device_code"],
                "endpoint_url": opcua_endpoint_url(device["ip"], port=port),
                "node": list(XIAOZHOU_SYNTEC_SCHEME_A_NODES),
            }
        )
    return out
