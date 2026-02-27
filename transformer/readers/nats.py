"""NATSReader — pulls a single message from a JetStream subject."""
from transformer.base import Reader


class NATSReader(Reader):
    """Pulls one message from a JetStream subject and acks it.
    For stream consumers, supply: subject, stream, consumer (durable name).
    """
    protocol = "nats"

    def __init__(self, nats_client) -> None:
        self._nats = nats_client

    async def read(self, source_config: dict) -> bytes:
        subject  = source_config["subject"]
        stream   = source_config.get("stream")
        timeout  = source_config.get("timeout", 5.0)

        js  = self._nats.js
        sub = await js.subscribe(subject, stream=stream)
        try:
            msg = await sub.next_msg(timeout=timeout)
            await msg.ack()
            return msg.data
        finally:
            await sub.unsubscribe()
