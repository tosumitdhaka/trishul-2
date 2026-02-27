"""VictoriaLogs EventStore implementation.

Pushes FM alarms and LOG entries as JSON Lines to /insert/jsonline.
Queries via LogsQL at /select/logsql/query.
"""

import json
import logging

import httpx

from core.models.envelope import FCAPSDomain, MessageEnvelope
from core.storage.base import EventStore

log = logging.getLogger(__name__)


class VictoriaLogsEvents(EventStore):
    def __init__(self, url: str) -> None:
        self._base_url = url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def startup(self) -> None:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10.0)

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()

    def _to_log_line(self, envelope: MessageEnvelope) -> str:
        doc = {
            "_time":       envelope.timestamp.isoformat(),
            "_msg":        envelope.normalized.get("message", f"{envelope.protocol} event from {envelope.source_ne}"),
            "domain":      envelope.domain,
            "protocol":    envelope.protocol,
            "source_ne":   envelope.source_ne,
            "direction":   envelope.direction,
            "severity":    envelope.severity,
            "envelope_id": envelope.id,
            "trace_id":    envelope.trace_id,
            **{k: v for k, v in envelope.normalized.items() if isinstance(v, (str, int, float, bool))},
        }
        return json.dumps({k: v for k, v in doc.items() if v is not None})

    async def _write(self, envelope: MessageEnvelope) -> None:
        if not self._client:
            raise RuntimeError("VictoriaLogs client not initialised")
        line = self._to_log_line(envelope)
        await self._client.post(
            "/insert/jsonline",
            content=line,
            params={"_stream_fields": "protocol,source_ne,domain"},
            headers={"Content-Type": "application/stream+json"},
        )

    async def write_fm(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def write_log(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def search(
        self,
        query: str,
        domain: str,
        start: str  = "-6h",
        end: str    = "now",
        limit: int  = 100,
    ) -> list[dict]:
        if not self._client:
            raise RuntimeError("VictoriaLogs client not initialised")
        logsql = f"{query} AND domain:{domain}"
        resp = await self._client.get(
            "/select/logsql/query",
            params={"query": logsql, "start": start, "end": end, "limit": limit},
        )
        resp.raise_for_status()
        return [json.loads(line) for line in resp.text.strip().splitlines() if line]

    async def health(self) -> bool:
        if not self._client:
            return False
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False
