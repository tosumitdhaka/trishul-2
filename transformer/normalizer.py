"""FCAPSNormalizer — the single shared Normalizer for all protocols.

Every protocol Decoder outputs a plain dict.
This Normalizer maps it to a canonical MessageEnvelope.

meta dict keys (set by the calling plugin):
  domain       — FCAPSDomain value (required)
  protocol     — protocol string (required)
  source_ne    — NE identifier (falls back to decoded field)
  direction    — Direction value (default: inbound)
  raw_payload  — original inbound data
  trace_id     — request trace ID
  tags         — list of tag strings
"""

from core.models.envelope import Direction, MessageEnvelope, Severity
from transformer.base import Normalizer


class FCAPSNormalizer(Normalizer):
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope:
        severity_raw = decoded.get("severity") or meta.get("severity")
        severity     = Severity(severity_raw) if severity_raw else None

        return MessageEnvelope(
            domain      = meta["domain"],
            protocol    = meta["protocol"],
            source_ne   = meta.get("source_ne") or decoded.get("source_ne", "unknown"),
            direction   = meta.get("direction", Direction.INBOUND),
            severity    = severity,
            raw_payload = meta.get("raw_payload", {}),
            normalized  = decoded,
            trace_id    = meta.get("trace_id"),
            tags        = meta.get("tags", []),
        )
