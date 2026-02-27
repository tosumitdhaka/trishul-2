"""Envelope publishing helpers.

Plugins call publish_envelope() after validating inbound data.
The raw payload + metadata are published to fcaps.ingest.{protocol}.
"""

import json
import logging

from core.bus.client import get_js
from core.models.envelope import MessageEnvelope

log = logging.getLogger(__name__)


async def publish_envelope(envelope: MessageEnvelope) -> None:
    """Publish a MessageEnvelope to fcaps.ingest.{protocol}.

    The transformer-worker NATS consumer picks this up asynchronously.
    HTTP handler returns 202 without waiting for this to complete processing.
    """
    subject = f"fcaps.ingest.{envelope.protocol}"
    payload = envelope.model_dump_json().encode()
    js = get_js()
    ack = await js.publish(subject, payload)
    log.info(
        "envelope_ingested",
        extra={
            "envelope_id": envelope.id,
            "protocol":    envelope.protocol,
            "domain":      envelope.domain,
            "subject":     subject,
            "nats_seq":    ack.seq,
        },
    )


async def publish_sim(envelope: MessageEnvelope) -> None:
    """Publish a simulated envelope to fcaps.sim.{protocol} for audit."""
    subject = f"fcaps.sim.{envelope.protocol}"
    payload = envelope.model_dump_json().encode()
    js = get_js()
    await js.publish(subject, payload)
