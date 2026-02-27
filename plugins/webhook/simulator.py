"""Synthetic webhook event generator for /simulate endpoint."""

import random
import uuid
from datetime import datetime, timezone

from plugins.webhook.models import SimulateRequest

_SEVERITIES = ["CRITICAL", "MAJOR", "MINOR", "WARNING", "CLEARED"]
_MESSAGES   = [
    "Link down on interface GE0/0",
    "CPU utilization exceeded 90%",
    "Memory threshold breach",
    "BGP session dropped",
    "Interface flapping detected",
]


def generate_events(req: SimulateRequest) -> list[dict]:
    """Generate `count` synthetic webhook payloads."""
    events = []
    for _ in range(req.count):
        events.append({
            "source_ne":  req.source_ne,
            "domain":     req.domain,
            "severity":   req.severity if req.domain == "FM" else None,
            "message":    random.choice(_MESSAGES),
            "data": {
                "event_id":   str(uuid.uuid4()),
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "metric_val": round(random.uniform(0, 100), 2),
            },
        })
    return events
