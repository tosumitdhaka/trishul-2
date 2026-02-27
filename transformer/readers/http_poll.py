"""HTTPPollReader — periodic HTTP GET to an external endpoint."""
import httpx
from transformer.base import Reader


class HTTPPollReader(Reader):
    protocol = "http_poll"

    async def read(self, source_config: dict) -> bytes:
        url     = source_config["url"]
        headers = source_config.get("headers", {})
        timeout = source_config.get("timeout", 10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.content
