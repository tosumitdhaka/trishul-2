"""ProtobufEncoder — MessageEnvelope → protobuf bytes.
Phase 2 scaffold: falls back to JSON bytes until dynamic .proto is wired.
"""
from transformer.base import Encoder
from core.models.envelope import MessageEnvelope


class ProtobufEncoder(Encoder):
    format = "protobuf"

    async def encode(self, envelope: MessageEnvelope) -> bytes:
        # Phase 2 scaffold: JSON fallback until dynamic proto schema is registered
        return envelope.model_dump_json().encode("utf-8")
