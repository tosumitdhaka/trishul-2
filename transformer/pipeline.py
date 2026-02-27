"""TransformPipeline and PipelineRegistry — Phase 1 stubs.

TransformPipeline: assembled per-request or at plugin startup.
  run()             — for plugin-bound pipelines (data already in hand)
  run_with_reader() — for ad-hoc / async job pipelines (Reader fetches data)

PipelineRegistry: singleton, holds all registered stage implementations.
  Plugins call register_decoder() etc. at on_startup().
  TransformRouter (Phase 2) calls get_pipeline() to build ad-hoc pipelines.
"""

from __future__ import annotations

from typing import Any

from transformer.base import Decoder, Encoder, Normalizer, Reader, Writer
from core.models.envelope import MessageEnvelope


class TransformPipeline:
    """Assembles and executes a single Reader→Decoder→Normalizer→Encoder→Writer pipeline."""

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
        meta:        dict[str, Any],
        sink_config: dict[str, Any],
    ) -> MessageEnvelope:
        """Execute pipeline with pre-fetched raw data (plugin-bound path)."""
        decoded  = await self.decoder.decode(raw)
        envelope = await self.normalizer.normalize(decoded, meta)
        encoded  = await self.encoder.encode(envelope)
        await self.writer.write(encoded, sink_config)
        return envelope

    async def run_with_reader(
        self,
        source_config: dict[str, Any],
        sink_config:   dict[str, Any],
    ) -> MessageEnvelope:
        """Execute full pipeline including Reader stage (ad-hoc/batch path)."""
        if not self.reader:
            raise RuntimeError("No Reader configured for this pipeline")
        raw = await self.reader.read(source_config)
        return await self.run(raw, source_config, sink_config)


class PipelineRegistry:
    """Singleton registry of all available pipeline stage implementations.

    Populated by plugins at startup via register_*() methods.
    Queried by TransformRouter (Phase 2) to assemble ad-hoc pipelines.
    """

    def __init__(self) -> None:
        self._readers:    dict[str, Reader]    = {}
        self._decoders:   dict[str, Decoder]   = {}
        self._encoders:   dict[str, Encoder]   = {}
        self._writers:    dict[str, Writer]    = {}
        self._normalizer: Normalizer | None    = None

    # ─── Registration ─────────────────────────────────────────────────────

    def register_reader(self, protocol: str, reader: Reader) -> None:
        self._readers[protocol] = reader

    def register_decoder(self, fmt: str, decoder: Decoder) -> None:
        self._decoders[fmt] = decoder

    def register_encoder(self, fmt: str, encoder: Encoder) -> None:
        self._encoders[fmt] = encoder

    def register_writer(self, target: str, writer: Writer) -> None:
        self._writers[target] = writer

    def set_normalizer(self, normalizer: Normalizer) -> None:
        self._normalizer = normalizer

    # ─── Lookup ───────────────────────────────────────────────────────────

    def get_decoder(self, fmt: str) -> Decoder:
        if fmt not in self._decoders:
            raise KeyError(f"No decoder registered for format: '{fmt}'")
        return self._decoders[fmt]

    def get_encoder(self, fmt: str) -> Encoder:
        if fmt not in self._encoders:
            raise KeyError(f"No encoder registered for format: '{fmt}'")
        return self._encoders[fmt]

    def get_writer(self, target: str) -> Writer:
        if target not in self._writers:
            raise KeyError(f"No writer registered for target: '{target}'")
        return self._writers[target]

    def get_normalizer(self) -> Normalizer:
        if not self._normalizer:
            raise RuntimeError("No normalizer set in PipelineRegistry")
        return self._normalizer

    def list_stages(self) -> dict:
        return {
            "readers":  list(self._readers.keys()),
            "decoders": list(self._decoders.keys()),
            "encoders": list(self._encoders.keys()),
            "writers":  list(self._writers.keys()),
        }


# Module-level singleton — imported by plugins and app factory
pipeline_registry = PipelineRegistry()
