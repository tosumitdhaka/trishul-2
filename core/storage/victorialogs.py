from __future__ import annotations

import json
import logging
from datetime import datetime

import httpx

from core.models.envelope import MessageEnvelope
from core.storage.base import EventStore

log = logging.getLogger(__name__)

_INSERT_PATH  = "/insert/jsonline"
_SELECT_PATH  = "/select/logsql/query"
_STREAM_FIELDS = "protocol,source_ne,domain"


class VictoriaLogsEvents(EventStore):
    def __init__(self, url: str) -> None:
        self._url = url.rstrip("/")

    async def _write(self, envelope: MessageEnvelope, msg: str) -> None:
        doc = {
            "_time":       envelope.timestamp.isoformat(),
            "_msg":        msg,
            "domain":      envelope.domain,
            "protocol":    envelope.protocol,
            "source_ne":   envelope.source_ne,
            "severity":    envelope.severity,
            "envelope_id": envelope.id,
            "direction":   envelope.direction,
            "trace_id":    envelope.trace_id,
            **envelope.normalized,
        }
        line = json.dumps(doc) + "\n"
        url = f"{self._url}{_INSERT_PATH}?_stream_fields={_STREAM_FIELDS}&_time_field=_time&_msg_field=_msg"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, content=line.encode(),
                                     headers={"Content-Type": "application/stream+json"})
            resp.raise_for_status()
        log.info("event=storage_write envelope_id=%s domain=%s", envelope.id, envelope.domain)

    async def write_fm(self, envelope: MessageEnvelope) -> None:
        msg = f"{envelope.severity or 'UNKNOWN'} alarm from {envelope.source_ne}"
        await self._write(envelope, msg)

    async def write_log(self, envelope: MessageEnvelope) -> None:
        msg = str(envelope.normalized.get("message", f"Log from {envelope.source_ne}"))
        await self._write(envelope, msg)

    async def search(
        self,
        query: str,
        domain: str,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[dict]:
        params = {
            "query": f'domain:{domain} AND ({query})',
            "start": start.isoformat(),
            "end":   end.isoformat(),
            "limit": str(limit),
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._url}{_SELECT_PATH}", params=params)
            resp.raise_for_status()
        return resp.json()

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self._url}/health")
                return resp.status_code == 200
        except Exception:
            return False
