"""JSONEncoder — MessageEnvelope → JSON bytes."""
import json
from transformer.base import Encoder
from core.models.envelope import MessageEnvelope


class JSONEncoder(Encoder):
    format = "json"

    async def encode(self, envelope: MessageEnvelope) -> bytes:
        return envelope.model_dump_json().encode("utf-8")
