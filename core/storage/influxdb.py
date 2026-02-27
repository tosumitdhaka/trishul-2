from __future__ import annotations

import logging
from datetime import datetime

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from core.models.envelope import MessageEnvelope
from core.storage.base import MetricsStore

log = logging.getLogger(__name__)


class InfluxDBMetrics(MetricsStore):
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self._url    = url
        self._token  = token
        self._org    = org
        self._bucket = bucket

    def _client(self) -> InfluxDBClientAsync:
        return InfluxDBClientAsync(
            url=self._url, token=self._token, org=self._org
        )

    async def write_pm(self, envelope: MessageEnvelope) -> None:
        record = (
            f"pm_metrics,"
            f"protocol={envelope.protocol},"
            f"source_ne={envelope.source_ne},"
            f"domain={envelope.domain} "
            f"value=1.0 "
            f"{int(envelope.timestamp.timestamp() * 1_000_000_000)}"
        )
        async with self._client() as c:
            write_api = c.write_api()
            await write_api.write(bucket=self._bucket, record=record)
        log.info("event=storage_write_pm envelope_id=%s", envelope.id)

    async def query_pm(
        self,
        source_ne: str,
        start: datetime,
        end: datetime,
        metric_name: str | None = None,
    ) -> list[dict]:
        flux = (
            f'from(bucket:"{self._bucket}")'
            f" |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)"
            f' |> filter(fn: (r) => r["source_ne"] == "{source_ne}")'
        )
        if metric_name:
            flux += f' |> filter(fn: (r) => r["metric_name"] == "{metric_name}")'
        async with self._client() as c:
            tables = await c.query_api().query(flux, org=self._org)
        results = []
        for table in tables:
            for record in table.records:
                results.append({"time": str(record.get_time()), "value": record.get_value()})
        return results

    async def health(self) -> bool:
        try:
            async with self._client() as c:
                return await c.ping()
        except Exception:
            return False
