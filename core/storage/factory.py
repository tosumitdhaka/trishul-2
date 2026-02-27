"""Storage factory — returns (MetricsStore, EventStore) based on STORAGE_MODE.

Add new storage backends here without touching any other code.
"""

from core.config.settings import Settings
from core.storage.base import EventStore, MetricsStore
from core.storage.influxdb import InfluxDBMetrics
from core.storage.victorialogs import VictoriaLogsEvents


async def get_stores(settings: Settings) -> tuple[MetricsStore, EventStore]:
    """Instantiate and warm up storage adapters for the given mode."""
    if settings.storage_mode in ("lab", "prod"):
        metrics = InfluxDBMetrics(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
            bucket=settings.influx_bucket,
        )
        events = VictoriaLogsEvents(url=settings.victoria_url)
    else:
        raise ValueError(f"Unknown STORAGE_MODE: {settings.storage_mode}")

    await metrics.startup()
    await events.startup()
    return metrics, events
