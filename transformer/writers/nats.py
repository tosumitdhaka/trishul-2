"""NATSWriter — publishes encoded bytes to a NATS JetStream subject."""
from transformer.base import Writer


class NATSWriter(Writer):
    """sink_config keys: subject (required), stream (optional)."""
    target = "nats"

    def __init__(self, nats_client) -> None:
        self._nats = nats_client

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        subject = sink_config.get("subject", "fcaps.done.nats")
        if isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")
        await self._nats.js.publish(subject, data)
