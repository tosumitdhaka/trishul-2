"""CSVWriter — appends CSV bytes to a local file path."""
from __future__ import annotations
from pathlib import Path
from transformer.base import Writer


class CSVWriter(Writer):
    """sink_config keys: path (required), mode ('append'|'overwrite', default 'append')."""
    target = "csv"

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        if isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")

        path = Path(sink_config["path"])
        path.parent.mkdir(parents=True, exist_ok=True)

        mode = "ab" if sink_config.get("mode", "append") == "append" else "wb"
        with open(path, mode) as f:
            f.write(data)
            if not data.endswith(b"\n"):
                f.write(b"\n")
