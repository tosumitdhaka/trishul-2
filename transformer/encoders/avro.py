"""AvroEncoder — MessageEnvelope.normalized dict → Avro binary bytes."""
import io
from transformer.base import Encoder
from core.models.envelope import MessageEnvelope


class AvroEncoder(Encoder):
    format = "avro"

    def __init__(self, schema: dict | None = None) -> None:
        self._schema = schema  # parsed fastavro schema dict

    async def encode(self, envelope: MessageEnvelope) -> bytes:
        try:
            import fastavro
        except ImportError as exc:
            raise ImportError("AvroEncoder requires 'fastavro': pip install fastavro") from exc

        if self._schema is None:
            raise ValueError("AvroEncoder: no schema provided")

        record = envelope.normalized
        buf    = io.BytesIO()
        fastavro.writer(buf, self._schema, [record])
        return buf.getvalue()
