"""Generates synthetic webhook events for simulation."""
import random
import uuid
from datetime import datetime, timezone

from plugins.webhook.models import WebhookPayload

FAULT_TYPES  = ["linkDown", "linkUp", "nodeUnreachable", "highCpuUsage", "memoryThreshold"]
SEVERITIES   = ["CRITICAL", "MAJOR", "MINOR", "WARNING", "CLEARED"]


def generate_events(count: int, domain: str, severity: str, source_ne: str) -> list[WebhookPayload]:
    events = []
    for i in range(count):
        fault = random.choice(FAULT_TYPES)
        sev   = severity if severity != "RANDOM" else random.choice(SEVERITIES)
        events.append(WebhookPayload(
            source_ne = source_ne,
            domain    = domain,
            protocol  = "webhook",
            severity  = sev,
            message   = f"{fault} detected on {source_ne} (event {i+1}/{count})",
            data      = {
                "fault_type":  fault,
                "event_id":    str(uuid.uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        ))
    return events
