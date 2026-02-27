"""FileReader — reads raw bytes from a local/mounted file path."""
from pathlib import Path
from transformer.base import Reader


class FileReader(Reader):
    protocol = "file"

    async def read(self, source_config: dict) -> bytes:
        path = Path(source_config["path"])
        if not path.exists():
            raise FileNotFoundError(f"FileReader: {path} not found")
        return path.read_bytes()
