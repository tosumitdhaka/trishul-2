"""InfluxDB v2 MetricsStore implementation."""
from __future__ import annotations

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from core.config.settings import get_settings
from core.models.envelope import MessageEnvelope
from core.storage.base import MetricsStore


class InfluxDBMetrics(MetricsStore):
    def __init__(self) -> None:
        s = get_settings()
        self._client = InfluxDBClientAsync(
            url=s.INFLUX_URL,
            token=s.INFLUX_TOKEN,
            org=s.INFLUX_ORG,
        )
        self._bucket = s.INFLUX_BUCKET
        self._org    = s.INFLUX_ORG

    async def write_pm(self, envelope: MessageEnvelope) -> None:
        norm = envelope.normalized
        measurement = "pm_metrics"
        tags  = f'protocol={envelope.protocol},source_ne={envelope.source_ne}'
        value = norm.get("value", 0.0)
        ts_ns = int(envelope.timestamp.timestamp() * 1e9)
        line  = f"{measurement},{tags} value={value} {ts_ns}"

        async with self._client.write_api() as writer:
            await writer.write(bucket=self._bucket, record=line)

    async def query_pm(
        self,
        source_ne: str,
        start: str = "-1h",
        end: str   = "now()",
        metric_name: str | None = None,
        limit: int = 500,
    ) -> list[dict]:
        filter_ne    = f'|> filter(fn: (r) => r["source_ne"] == "{source_ne}")'
        filter_extra = (
            f'|> filter(fn: (r) => r["metric_name"] == "{metric_name}")'
            if metric_name else ""
        )
        flux = (
            f'from(bucket: "{self._bucket}")'
            f'  |> range(start: {start}, stop: {end})'
            f'  {filter_ne}'
            f'  {filter_extra}'
            f'  |> limit(n: {limit})'
        )
        async with self._client.query_api() as q:
            result = await q.query(flux, org=self._org)
        rows = []
        for table in result:
            for record in table.records:
                rows.append({"time": str(record.get_time()), "value": record.get_value()})
        return rows

    async def health(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False
