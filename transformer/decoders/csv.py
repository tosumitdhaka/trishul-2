"""CSVDecoder — bytes/str CSV → list[dict] wrapped under 'rows' key."""
import csv
import io
from transformer.base import Decoder


class CSVDecoder(Decoder):
    format = "csv"

    async def decode(self, raw: bytes | str) -> dict:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(raw))
        rows   = [dict(row) for row in reader]
        if not rows:
            raise ValueError("CSVDecoder: empty CSV or no header row")
        return {"rows": rows, "count": len(rows), "columns": list(rows[0].keys())}
