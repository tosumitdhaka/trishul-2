"""WebhookWriter — HTTP POST encoded payload to a target URL."""
import httpx
from transformer.base import Writer


class WebhookWriter(Writer):
    """sink_config keys: url (required), headers (optional), timeout (optional)."""
    target = "webhook"

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        url     = sink_config["url"]
        headers = sink_config.get("headers", {"Content-Type": "application/json"})
        timeout = sink_config.get("timeout", 10.0)

        if isinstance(data, dict):
            content = json.dumps(data).encode("utf-8")
        else:
            content = data

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, content=content, headers=headers)
            resp.raise_for_status()
