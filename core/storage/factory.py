from __future__ import annotations

from core.config.settings import Settings
from core.storage.base import EventStore, MetricsStore
from core.storage.influxdb import InfluxDBMetrics
from core.storage.victorialogs import VictoriaLogsEvents


def get_stores(settings: Settings) -> tuple[MetricsStore, EventStore]:
    """Factory — returns the correct store implementations for the configured mode."""
    # Both lab and prod use the same concrete adapters at this stage.
    # prod would point to clustered / remote endpoints via settings.
    metrics = InfluxDBMetrics(
        url=settings.influx_url,
        token=settings.influx_token,
        org=settings.influx_org,
        bucket=settings.influx_bucket,
    )
    events = VictoriaLogsEvents(url=settings.victoria_url)
    return metrics, events
