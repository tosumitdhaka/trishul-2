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
            "_msg":        envelope.normalized.get("message", "") or str(envelope.normalized),
            "domain":      envelope.domain,
            "protocol":    envelope.protocol,
            "source_ne":   envelope.source_ne,
            "severity":    envelope.severity,
            "envelope_id": envelope.id,
            "direction":   envelope.direction,
            "trace_id":    envelope.trace_id or "",
            **{k: str(v) for k, v in envelope.normalized.items()},
        }
        doc = {k: v for k, v in doc.items() if v is not None}
        url = f"{self._base_url}/insert/jsonline?_stream_fields=protocol,source_ne,domain"
        resp = await self._client.post(
            url, content=json.dumps(doc),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    async def write_fm(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def write_log(self, envelope: MessageEnvelope) -> None:
        await self._write(envelope)

    async def search(
        self,
        query:  str,
        domain: str | None = None,   # None → no domain filter (returns FM+LOG)
        start:  str = "-1h",
        end:    str = "now",
        limit:  int = 200,
    ) -> list[dict]:
        """Search VictoriaLogs using LogsQL.

        If domain is None the query is sent as-is (no domain: filter prepended),
        allowing cross-domain searches.
        """
        if domain:
            q = query.strip()
            full_query = f"domain:{domain}" if not q or q == "*" else f"domain:{domain} AND ({q})"
        else:
            q = query.strip()
            full_query = q if q and q != "*" else "*"

        params = {
            "query": full_query,
            "start": start,
            "end":   end,
            "limit": str(limit),
        }
        resp = await self._client.get(
            f"{self._base_url}/select/logsql/query", params=params
        )
        resp.raise_for_status()
        return [
            json.loads(line)
            for line in resp.text.strip().splitlines()
            if line
        ]

    async def health(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/health")
            return resp.status_code == 200
        except Exception:
            return False
