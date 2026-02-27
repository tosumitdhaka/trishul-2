"""VictoriaLogs EventStore implementation."""
from __future__ import annotations

import json
import httpx

from core.config.settings import get_settings
from core.models.envelope import MessageEnvelope
from core.storage.base import EventStore


class VictoriaLogsEvents(EventStore):
    def __init__(self) -> None:
        s = get_settings()
        self._base_url = s.VICTORIA_URL.rstrip("/")
        self._client   = httpx.AsyncClient(timeout=10.0)

    async def _write(self, envelope: MessageEnvelope) -> None:
        doc = {
            "_time":       envelope.timestamp.isoformat(),
            "_msg":        envelope.normalized.get("message", ""),
            "domain":      envelope.domain.value,
            "protocol":    envelope.protocol,
            "source_ne":   envelope.source_ne,
            "severity":    envelope.severity.value if envelope.severity else None,
            "envelope_id": envelope.id,
            "direction":   envelope.direction.value,
            "trace_id":    envelope.trace_id,
            **envelope.normalized,
        }
        url = (
            f"{self._base_url}/insert/jsonline"
            f"?_stream_fields=protocol,source_ne,domain"
        )
        await self._client.post(url, content=json.dumps(doc), headers={"Content-Type": "application/json"})

    async def write_fm(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def write_log(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def search(
        self,
        query: str,
        domain: str   = "FM",
        start: str    = "-6h",
        end: str      = "now",
        limit: int    = 100,
    ) -> list[dict]:
        params = {
            "query": f"domain:{domain} AND ({query})",
            "start": start,
            "end":   end,
            "limit": str(limit),
        }
        resp = await self._client.get(f"{self._base_url}/select/logsql/query", params=params)
        resp.raise_for_status()
        return [json.loads(line) for line in resp.text.strip().splitlines() if line]

    async def health(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/health")
            return resp.status_code == 200
        except Exception:
            return False
