"""Abstract base classes for all Transformer pipeline stages.
Implementations live in transformer/decoders/, encoders/, readers/, writers/.
All ABCs are defined here so plugins can import stage types without
creating circular dependencies.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models.envelope import MessageEnvelope


class Reader(ABC):
    """Fetches raw data from a source."""
    protocol: str

    @abstractmethod
    async def read(self, source_config: dict[str, Any]) -> bytes | dict: ...


class Decoder(ABC):
    """Converts raw bytes/dict into a plain decoded dict."""
    format: str

    @abstractmethod
    async def decode(self, raw: bytes | dict) -> dict: ...


class Normalizer(ABC):
    """Maps a decoded dict + metadata into a MessageEnvelope."""

    @abstractmethod
    async def normalize(self, decoded: dict, meta: dict[str, Any]) -> MessageEnvelope: ...


class Encoder(ABC):
    """Serialises a MessageEnvelope into the output format."""
    format: str

    @abstractmethod
    async def encode(self, envelope: MessageEnvelope) -> bytes | dict: ...


class Writer(ABC):
    """Writes encoded data to a sink."""
    target: str

    @abstractmethod
    async def write(self, data: bytes | dict, sink_config: dict[str, Any]) -> None: ...
