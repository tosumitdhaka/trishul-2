"""TransformPipeline assembler + PipelineRegistry.

Phase 1: Structure + registry defined. Implementations wired in Phase 2.
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel

from transformer.base import Decoder, Normalizer, Encoder, Writer, Reader
from core.models.envelope import MessageEnvelope


class StageConfig(BaseModel):
    type: str
    model_config = {"extra": "allow"}


class NormalizerConfig(BaseModel):
    domain:    str
    protocol:  str
    source_ne: str
    direction: str = "inbound"


class PipelineJobConfig(BaseModel):
    reader:     StageConfig | None = None
    decoder:    StageConfig
    normalizer: NormalizerConfig
    encoder:    StageConfig
    writer:     StageConfig


class TransformPipeline:
    """Assembles and runs a Reader→Decoder→Normalizer→Encoder→Writer pipeline."""

    def __init__(
        self,
        decoder:    Decoder,
        normalizer: Normalizer,
        encoder:    Encoder,
        writer:     Writer,
        reader:     Reader | None = None,
    ) -> None:
        self.reader     = reader
        self.decoder    = decoder
        self.normalizer = normalizer
        self.encoder    = encoder
        self.writer     = writer

    async def run(
        self,
        raw:         bytes | dict,
        meta:        dict,
        sink_config: dict,
    ) -> MessageEnvelope:
        """Run pipeline on already-available raw data (no Reader needed)."""
        decoded  = await self.decoder.decode(raw)
        envelope = await self.normalizer.normalize(decoded, meta)
        encoded  = await self.encoder.encode(envelope)
        await self.writer.write(encoded, sink_config)
        return envelope

    async def run_with_reader(
        self,
        source_config: dict,
        sink_config:   dict,
    ) -> MessageEnvelope:
        """Run full pipeline including Reader stage (ad-hoc / batch jobs)."""
        if self.reader is None:
            raise ValueError("No Reader configured for this pipeline")
        raw = await self.reader.read(source_config)
        return await self.run(raw, source_config, sink_config)


class PipelineRegistry:
    """Auto-discovers and holds all registered stage implementations."""

    def __init__(self) -> None:
        self._decoders:  dict[str, Decoder]  = {}
        self._encoders:  dict[str, Encoder]  = {}
        self._readers:   dict[str, Reader]   = {}
        self._writers:   dict[str, Writer]   = {}

    def register_decoder(self, name: str, impl: Decoder)  -> None: self._decoders[name]  = impl
    def register_encoder(self, name: str, impl: Encoder)  -> None: self._encoders[name]  = impl
    def register_reader(self,  name: str, impl: Reader)   -> None: self._readers[name]   = impl
    def register_writer(self,  name: str, impl: Writer)   -> None: self._writers[name]   = impl

    def get_pipeline(self, config: PipelineJobConfig, normalizer: Normalizer) -> TransformPipeline:
        decoder = self._decoders.get(config.decoder.type)
        encoder = self._encoders.get(config.encoder.type)
        writer  = self._writers.get(config.writer.type)
        reader  = self._readers.get(config.reader.type) if config.reader else None

        missing = [n for n, v in [("decoder", decoder), ("encoder", encoder), ("writer", writer)] if v is None]
        if missing:
            raise ValueError(f"Unregistered pipeline stages: {missing}")

        return TransformPipeline(
            decoder=decoder, normalizer=normalizer,
            encoder=encoder, writer=writer, reader=reader,
        )

    def list_stages(self) -> dict:
        return {
            "decoders": list(self._decoders.keys()),
            "encoders": list(self._encoders.keys()),
            "readers":  list(self._readers.keys()),
            "writers":  list(self._writers.keys()),
        }


# Module-level singleton — used by all plugins
pipeline_registry = PipelineRegistry()
