"""ProtobufDecoder — raw protobuf bytes → dict via schema registry.

Uses google.protobuf.descriptor_pool + descriptor_pb2 for dynamic message loading.
Schema must be pre-registered in the SQLite schema registry.
"""
from __future__ import annotations
import json
from transformer.base import Decoder


class ProtobufDecoder(Decoder):
    """Decodes protobuf bytes using a schema_id from the registry.

    For Phase 2 lab use: if google-protobuf is unavailable or schema is not
    registered, falls back to treating the payload as JSON bytes.
    """
    format = "protobuf"

    def __init__(self, schema_registry=None) -> None:
        self._registry = schema_registry  # SchemaRegistry instance, injected

    async def decode(self, raw: bytes | dict) -> dict:
        if isinstance(raw, dict):
            return raw  # already decoded upstream

        # Attempt protobuf decode if registry available
        if self._registry is not None:
            try:
                return await self._decode_proto(raw)
            except Exception as exc:
                import structlog
                structlog.get_logger(__name__).warning(
                    "protobuf_decode_fallback", error=str(exc)
                )

        # Fallback: try JSON
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"ProtobufDecoder: cannot decode payload — {exc}") from exc

    async def _decode_proto(self, raw: bytes) -> dict:
        """Dynamic protobuf decode using registered .proto descriptor.
        Requires google-protobuf to be installed.
        """
        from google.protobuf import descriptor_pool, descriptor_pb2, message_factory
        # Schema lookup would normally use schema_id from pipeline config
        # Phase 2: scaffold only — full impl in Phase 3 protocol plugins
        raise NotImplementedError("Dynamic .proto decode: register schema_id first")
