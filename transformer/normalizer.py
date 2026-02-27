from __future__ import annotations

from typing import Any

from transformer.base import Normalizer
from core.models.envelope import Direction, FCAPSDomain, MessageEnvelope, Severity


class FCAPSNormalizer(Normalizer):
    """
    Single shared Normalizer used by all protocol plugins.
    meta dict expected keys:
        domain       : str  (FM | PM | LOG)
        protocol     : str
        source_ne    : str  (optional — falls back to decoded['source_ne'])
        direction    : str  (optional, default 'inbound')
        severity     : str  (optional, FM only)
        raw_payload  : dict (original bytes/dict before decoding)
        trace_id     : str  (optional)
        tags         : list (optional)
    """

    async def normalize(
        self,
        decoded: dict[str, Any],
        meta:    dict[str, Any],
    ) -> MessageEnvelope:
        source_ne = (
            meta.get("source_ne")
            or decoded.get("source_ne")
            or decoded.get("sourceId")
            or "unknown"
        )
        severity_raw = meta.get("severity") or decoded.get("severity")
        try:
            severity = Severity(severity_raw.upper()) if severity_raw else None
        except (ValueError, AttributeError):
            severity = None

        return MessageEnvelope(
            domain      = FCAPSDomain(meta["domain"]),
            protocol    = meta["protocol"],
            source_ne   = source_ne,
            direction   = Direction(meta.get("direction", Direction.INBOUND)),
            severity    = severity,
            raw_payload = meta.get("raw_payload", {}),
            normalized  = decoded,
            trace_id    = meta.get("trace_id"),
            tags        = meta.get("tags", []),
        )
