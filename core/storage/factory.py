"""StorageFactory — returns (MetricsStore, EventStore) for given mode."""
from core.storage.base import MetricsStore, EventStore


def get_stores(mode: str) -> tuple[MetricsStore, EventStore]:
    """lab | prod both use InfluxDB + VictoriaLogs.
    Factory exists so tests can inject mock stores."""
    from core.storage.influxdb import InfluxDBMetrics
    from core.storage.victorialogs import VictoriaLogsEvents
    return InfluxDBMetrics(), VictoriaLogsEvents()
