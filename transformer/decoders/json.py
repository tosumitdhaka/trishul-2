"""JSONDecoder — bytes | str | dict → dict."""
import json as _json
from transformer.base import Decoder


class JSONDecoder(Decoder):
    format = "json"

    async def decode(self, raw: bytes | str | dict) -> dict:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        try:
            result = _json.loads(raw)
        except _json.JSONDecodeError as exc:
            raise ValueError(f"JSONDecoder: invalid JSON — {exc}") from exc
        if not isinstance(result, dict):
            raise ValueError(f"JSONDecoder: expected object, got {type(result).__name__}")
        return result
