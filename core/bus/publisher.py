from __future__ import annotations

import json
import logging

from nats.aio.client import Client as NATSClient

from core.models.envelope import MessageEnvelope

log = logging.getLogger(__name__)


async def publish_envelope(
    nc: NATSClient,
    envelope: MessageEnvelope,
    subject_prefix: str = "fcaps.ingest",
) -> None:
    """
    Serialise and publish a MessageEnvelope to JetStream.

    Subject: {subject_prefix}.{protocol}
    e.g.  fcaps.ingest.webhook
          fcaps.sim.snmp
    """
    subject = f"{subject_prefix}.{envelope.protocol}"
    payload = envelope.model_dump_json().encode()
    js = nc.jetstream()
    ack = await js.publish(subject, payload)
    log.info(
        "event=envelope_ingested envelope_id=%s subject=%s seq=%s",
        envelope.id, subject, ack.seq,
    )
