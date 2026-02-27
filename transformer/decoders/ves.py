"""VESDecoder — VES 7.x event JSON → normalised flat dict.

Validates presence of required VES 7.x fields then flattens
commonEventHeader + domain-specific body into a single dict.
"""
import json as _json
from transformer.base import Decoder

REQUIRED_HEADER_FIELDS = {
    "domain", "eventId", "eventName", "lastEpochMicrosec",
    "priority", "reportingEntityName", "sequence", "sourceName",
    "startEpochMicrosec", "version", "vesEventListenerVersion",
}


class VESDecoder(Decoder):
    """Decodes VES 7.x CommonEventFormat JSON."""
    format = "ves"

    async def decode(self, raw: bytes | str | dict) -> dict:
        if isinstance(raw, (bytes, bytearray)):
            raw = _json.loads(raw.decode("utf-8"))
        elif isinstance(raw, str):
            raw = _json.loads(raw)

        # VES envelope
        event = raw.get("event", raw)
        header = event.get("commonEventHeader", {})

        missing = REQUIRED_HEADER_FIELDS - set(header.keys())
        if missing:
            raise ValueError(f"VESDecoder: missing required header fields: {missing}")

        domain     = header["domain"]
        source_ne  = header.get("sourceName", "unknown")
        event_name = header.get("eventName", "")
        epoch_us   = header.get("lastEpochMicrosec", 0)

        # Flatten: header fields + domain body
        decoded = {
            "source_ne":   source_ne,
            "domain":      domain,
            "event_name":  event_name,
            "epoch_us":    epoch_us,
            "priority":    header.get("priority"),
            "sequence":    header.get("sequence"),
            "version":     header.get("version"),
            "ves_version": header.get("vesEventListenerVersion"),
            "message":     event_name,
        }

        # Attach domain-specific body under its key (faultFields, measurementFields, etc.)
        for key, value in event.items():
            if key != "commonEventHeader":
                decoded[key] = value

        # Map VES domain to FCAPS domain
        ves_to_fcaps = {
            "fault":       "FM",
            "measurement": "PM",
            "syslog":      "LOG",
            "log":         "LOG",
            "heartbeat":   "LOG",
            "notification": "FM",
            "other":       "LOG",
        }
        decoded["fcaps_domain"] = ves_to_fcaps.get(domain.lower(), "LOG")

        # Severity mapping for FM events
        if "faultFields" in event:
            ff  = event["faultFields"]
            sev_map = {
                "CRITICAL": "CRITICAL", "MAJOR": "MAJOR",
                "MINOR": "MINOR", "WARNING": "WARNING",
                "NORMAL": "CLEARED",
            }
            decoded["severity"] = sev_map.get(
                ff.get("eventSeverity", "").upper(), "WARNING"
            )
            decoded["alarm_condition"] = ff.get("alarmCondition")
            decoded["specific_problem"] = ff.get("specificProblem")

        return decoded
