"""publish_envelope() — the single helper all plugins use to publish to NATS."""
import json
from core.bus.client import TrishulNATSClient
from core.models.envelope import MessageEnvelope
from core.exceptions import BusPublishError


async def publish_envelope(
    nats_client: TrishulNATSClient,
    envelope: MessageEnvelope,
    subject: str,
) -> None:
    """Publish a MessageEnvelope to the given NATS subject as JSON."""
    try:
        payload = envelope.model_dump_json().encode()
        await nats_client.js.publish(subject, payload)
    except Exception as exc:
        raise BusPublishError(f"Failed to publish to {subject}: {exc}") from exc
