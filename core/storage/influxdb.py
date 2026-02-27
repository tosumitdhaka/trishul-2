"""InfluxDB v2 MetricsStore implementation.

Writes PM envelopes as line protocol points.
Measurement: pm_metrics
Tags:  protocol, source_ne, metric_name
Field: value (float)
"""

import logging

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write_api_async import WriteApiAsync
from influxdb_client.domain.write_precision import WritePrecision

from core.models.envelope import MessageEnvelope
from core.storage.base import MetricsStore

log = logging.getLogger(__name__)


class InfluxDBMetrics(MetricsStore):
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self._url    = url
        self._token  = token
        self._org    = org
        self._bucket = bucket
        self._client: InfluxDBClientAsync | None = None
        self._write_api: WriteApiAsync | None = None

    async def startup(self) -> None:
        self._client    = InfluxDBClientAsync(url=self._url, token=self._token, org=self._org)
        self._write_api = self._client.write_api()

    async def shutdown(self) -> None:
        if self._client:
            await self._client.close()

    async def write_pm(self, envelope: MessageEnvelope) -> None:
        if not self._write_api:
            raise RuntimeError("InfluxDB write_api not initialised")

        # Build one line-protocol point per normalized metric key
        points = []
        for metric_name, value in envelope.normalized.items():
            if not isinstance(value, (int, float)):
                continue
            point = (
                f"pm_metrics,"
                f"protocol={envelope.protocol},"
                f"source_ne={envelope.source_ne},"
                f"metric_name={metric_name} "
                f"value={float(value)}"
            )
            points.append(point)

        if points:
            await self._write_api.write(
                bucket=self._bucket,
                record="\n".join(points),
                write_precision=WritePrecision.NANOSECONDS,
            )

    async def query_pm(
        self,
        source_ne: str,
        start: str  = "-1h",
        end: str    = "now()",
        metric_name: str | None = None,
    ) -> list[dict]:
        if not self._client:
            raise RuntimeError("InfluxDB client not initialised")

        metric_filter = f'|> filter(fn: (r) => r["metric_name"] == "{metric_name}")' if metric_name else ""
        flux = f"""
        from(bucket: "{self._bucket}")
          |> range(start: {start}, stop: {end})
          |> filter(fn: (r) => r["_measurement"] == "pm_metrics")
          |> filter(fn: (r) => r["source_ne"] == "{source_ne}")
          {metric_filter}
        """
        tables = await self._client.query_api().query(flux)
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "time":        record.get_time().isoformat(),
                    "source_ne":   record.values.get("source_ne"),
                    "metric_name": record.values.get("metric_name"),
                    "value":       record.get_value(),
                })
        return results

    async def health(self) -> bool:
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
