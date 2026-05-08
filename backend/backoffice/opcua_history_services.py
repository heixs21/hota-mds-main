"""Helpers for OPC UA history sample data.

The collector pipeline that would normally populate
``OpcUaHistorySample`` is out of scope for the current iteration, so this
module lazily seeds a small batch of demo history samples whenever the
admin UI requests history for an OPC UA data source that has none yet.

This keeps the "历史数据" dialog functional in dev/demo environments
without requiring a separate management command.
"""
from __future__ import annotations

import math
import random
from datetime import timedelta

from django.utils import timezone

from .models import DataSourceConfig, OpcUaHistorySample


DEMO_SAMPLE_COUNT = 60
DEMO_INTERVAL_SECONDS = 60
DEFAULT_DEMO_NODE_ID = "ns=2;s=/Channel/State/chanStatus"
DEMO_QUALITY_CYCLE = (
    OpcUaHistorySample.QUALITY_GOOD,
    OpcUaHistorySample.QUALITY_GOOD,
    OpcUaHistorySample.QUALITY_GOOD,
    OpcUaHistorySample.QUALITY_UNCERTAIN,
    OpcUaHistorySample.QUALITY_GOOD,
    OpcUaHistorySample.QUALITY_BAD,
)


def ensure_opcua_history_samples(data_source: DataSourceConfig) -> None:
    """Populate demo OPC UA history rows for ``data_source`` if absent."""
    if data_source.source_type != "opcua":
        return
    if OpcUaHistorySample.objects.filter(data_source=data_source).exists():
        return

    configured_nodes = data_source.node if isinstance(data_source.node, list) else []
    first_configured_node = configured_nodes[0] if configured_nodes else ""
    connection_config = data_source.connection_config or {}
    node_id = (
        first_configured_node
        or connection_config.get("nodeId")
        or DEFAULT_DEMO_NODE_ID
    ).strip()

    rng = random.Random(f"opcua-history-{data_source.pk}")
    now = timezone.now().replace(microsecond=0)

    rows = []
    for offset in range(DEMO_SAMPLE_COUNT):
        sampled_at = now - timedelta(seconds=DEMO_INTERVAL_SECONDS * offset)
        base_value = 60 + 25 * math.sin(offset / 4.0)
        jitter = rng.uniform(-3.0, 3.0)
        value = round(base_value + jitter, 2)
        quality = DEMO_QUALITY_CYCLE[offset % len(DEMO_QUALITY_CYCLE)]
        rows.append(
            OpcUaHistorySample(
                data_source=data_source,
                node_id=node_id,
                value=str(value),
                quality=quality,
                sampled_at=sampled_at,
            )
        )

    OpcUaHistorySample.objects.bulk_create(rows)
