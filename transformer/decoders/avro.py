"""AvroDecoder — Avro binary bytes → dict via fastavro + schema registry."""
from __future__ import annotations
import io
from transformer.base import Decoder


class AvroDecoder(Decoder):
    format = "avro"

    def __init__(self, schema_registry=None) -> None:
        self._registry = schema_registry

    async def decode(self, raw: bytes | dict) -> dict:
        if isinstance(raw, dict):
            return raw

        try:
            import fastavro
        except ImportError as exc:
            raise ImportError("AvroDecoder requires 'fastavro': pip install fastavro") from exc

        schema = None
        if self._registry is not None:
            schema = await self._registry.get_parsed_schema("avro")

        buf    = io.BytesIO(raw)
        reader = fastavro.reader(buf, reader_schema=schema)
        records = list(reader)

        if not records:
            raise ValueError("AvroDecoder: no records in Avro payload")

        # Return first record as dict; multiple records wrapped under 'rows'
        if len(records) == 1:
            return dict(records[0])
        return {"rows": [dict(r) for r in records], "count": len(records)}
