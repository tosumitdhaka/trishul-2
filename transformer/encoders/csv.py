"""CSVEncoder — MessageEnvelope.normalized dict → CSV bytes (single row)."""
import csv
import io
from transformer.base import Encoder
from core.models.envelope import MessageEnvelope


class CSVEncoder(Encoder):
    format = "csv"

    async def encode(self, envelope: MessageEnvelope) -> bytes:
        data    = envelope.normalized
        buf     = io.StringIO()
        writer  = csv.DictWriter(buf, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow(data)
        return buf.getvalue().encode("utf-8")
