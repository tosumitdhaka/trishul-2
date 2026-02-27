"""WebhookReader — passthrough for data already in-hand from HTTP handler."""
from transformer.base import Reader


class WebhookReader(Reader):
    """No-op reader: data comes in via HTTP body, already in source_config['payload']."""
    protocol = "webhook"

    async def read(self, source_config: dict) -> dict:
        payload = source_config.get("payload")
        if payload is None:
            raise ValueError("WebhookReader: source_config must contain 'payload' key")
        return payload
