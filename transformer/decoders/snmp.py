"""SNMPDecoder — raw SNMP trap PDU bytes OR pre-parsed dict → normalised dict.

Supports two input formats:
  1. Pre-parsed dict (from pysnmp TrapReceiver — most common lab path)
  2. Raw bytes (full SNMP PDU — for future raw socket ingestion)
"""
from __future__ import annotations
from transformer.base import Decoder

# OID suffix → human-readable field name (minimal set for Phase 2)
OID_ALIAS = {
    "1.3.6.1.2.1.1.3.0":    "sysUpTime",
    "1.3.6.1.6.3.1.1.4.1.0": "snmpTrapOID",
    "1.3.6.1.2.1.2.2.1.1":  "ifIndex",
    "1.3.6.1.2.1.2.2.1.7":  "ifAdminStatus",
    "1.3.6.1.2.1.2.2.1.8":  "ifOperStatus",
}


class SNMPDecoder(Decoder):
    format = "snmp"

    async def decode(self, raw: bytes | dict) -> dict:
        if isinstance(raw, dict):
            return self._decode_parsed(raw)
        # Raw bytes path: try to decode as JSON first (for test payloads)
        # Full pysnmp PDU decoding is async-unfriendly — handled via pre-parsed dict path
        import json as _json
        try:
            parsed = _json.loads(raw.decode("utf-8"))
            return self._decode_parsed(parsed)
        except Exception:
            pass
        raise ValueError(
            "SNMPDecoder: raw bytes path requires pre-parsed dict. "
            "Pass pysnmp-decoded dict or JSON representation."
        )

    def _decode_parsed(self, data: dict) -> dict:
        """Normalise a pysnmp-style pre-parsed trap dict."""
        varbinds_raw = data.get("varbinds", data.get("var_binds", []))

        varbinds = {}
        for vb in varbinds_raw:
            if isinstance(vb, dict):
                oid = str(vb.get("oid", ""))
                val = vb.get("value", "")
            elif isinstance(vb, (list, tuple)) and len(vb) == 2:
                oid, val = str(vb[0]), str(vb[1])
            else:
                continue
            name = OID_ALIAS.get(oid, oid)
            varbinds[name] = val

        trap_oid = varbinds.get("snmpTrapOID", data.get("trap_oid", "unknown"))

        # Severity heuristic from trap OID suffix or explicit severity key
        severity = data.get("severity")
        if not severity:
            oid_lower = str(trap_oid).lower()
            if "linkdown" in oid_lower or "critical" in oid_lower:
                severity = "CRITICAL"
            elif "linkup" in oid_lower or "cleared" in oid_lower:
                severity = "CLEARED"
            elif "warning" in oid_lower:
                severity = "WARNING"
            else:
                severity = "MAJOR"

        return {
            "source_ne":  data.get("agent_address", data.get("source_ne", "unknown")),
            "trap_oid":   trap_oid,
            "severity":   severity,
            "message":    f"SNMP trap: {trap_oid}",
            "varbinds":   varbinds,
            "community":  data.get("community", "public"),
            "snmp_version": data.get("version", "v2c"),
        }
