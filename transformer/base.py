"""Abstract base classes for all Transformer pipeline stages.

Phase 1: ABCs only — no implementations here.
Phase 2: Concrete Decoder/Encoder/Reader/Writer implementations.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from core.models.envelope import MessageEnvelope


class Reader(ABC):
    """Reads raw data from an external source."""
    protocol: str

    @abstractmethod
    async def read(self, source_config: dict) -> bytes | dict:
        """Return raw bytes or dict from source."""
        ...


class Decoder(ABC):
    """Decodes raw bytes/dict into a plain Python dict."""
    format: str

    @abstractmethod
    async def decode(self, raw: bytes | dict) -> dict:
        ...


class Normalizer(ABC):
    """Converts a decoded dict + metadata into a MessageEnvelope."""

    @abstractmethod
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope:
        ...


class Encoder(ABC):
    """Encodes a MessageEnvelope into bytes or dict for output."""
    format: str

    @abstractmethod
    async def encode(self, envelope: MessageEnvelope) -> bytes | dict:
        ...


class Writer(ABC):
    """Writes encoded data to an output sink."""
    target: str

    @abstractmethod
    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        ...
