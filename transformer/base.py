"""Transformer stage ABCs — defined in Phase 1, implemented in Phase 2.

All five stages are abstract base classes. The only concrete implementation
in Phase 1 is FCAPSNormalizer (normalizer.py), used by the Webhook plugin.

Phase 2 fills in all Reader, Decoder, Encoder, Writer implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

from core.models.envelope import MessageEnvelope


class Reader(ABC):
    """Reads raw data from a source (SFTP, HTTP poll, NATS, file)."""
    protocol: str

    @abstractmethod
    async def read(self, source_config: dict[str, Any]) -> bytes | dict:
        """Fetch raw data from the configured source. Returns bytes or dict."""


class Decoder(ABC):
    """Decodes raw bytes/dict into a protocol-agnostic dict."""
    format: str

    @abstractmethod
    async def decode(self, raw: bytes | dict) -> dict:
        """Decode raw input to a plain dict of fields."""


class Normalizer(ABC):
    """Maps a decoded dict + metadata to a canonical MessageEnvelope."""

    @abstractmethod
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope:
        """Return a fully populated MessageEnvelope."""


class Encoder(ABC):
    """Encodes a MessageEnvelope to output bytes or dict."""
    format: str

    @abstractmethod
    async def encode(self, envelope: MessageEnvelope) -> bytes | dict:
        """Encode envelope for the target sink."""


class Writer(ABC):
    """Writes encoded data to a sink (NATS, InfluxDB, VictoriaLogs, SFTP, etc.)."""
    target: str

    @abstractmethod
    async def write(self, data: bytes | dict, sink_config: dict[str, Any]) -> None:
        """Persist or forward the encoded data."""
