"""FCAPSNormalizer — the single shared Normalizer implementation.
All protocol decoders output a plain dict; this maps it to a MessageEnvelope.
"""
import uuid
from datetime import datetime, timezone

from transformer.base import Normalizer
from core.models.envelope import MessageEnvelope, FCAPSDomain, Direction, Severity


class FCAPSNormalizer(Normalizer):
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope:
        domain_raw   = meta.get("domain", "LOG")
        direction_raw = meta.get("direction", "inbound")
        severity_raw  = decoded.get("severity") or meta.get("severity")

        return MessageEnvelope(
            id          = meta.get("envelope_id", str(uuid.uuid4())),
            timestamp   = meta.get("timestamp", datetime.now(timezone.utc)),
            domain      = FCAPSDomain(domain_raw),
            protocol    = meta.get("protocol", "unknown"),
            source_ne   = meta.get("source_ne") or decoded.get("source_ne", "unknown"),
            direction   = Direction(direction_raw),
            severity    = Severity(severity_raw) if severity_raw else None,
            raw_payload = meta.get("raw_payload", {}),
            normalized  = decoded,
            trace_id    = meta.get("trace_id"),
            tags        = meta.get("tags", []),
        )


# Shared singleton — imported by plugins
fcaps_normalizer = FCAPSNormalizer()
