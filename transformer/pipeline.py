"""TransformPipeline + PipelineRegistry.
Stubs in Phase 1 — fully populated in Phase 2 when decoder/encoder/writer
implementations are added.
"""
from __future__ import annotations

import logging
from typing import Any

from transformer.base import Decoder, Encoder, Normalizer, Reader, Writer
from core.models.envelope import MessageEnvelope

log = logging.getLogger(__name__)


class TransformPipeline:
    """
    Assembles and runs a Reader → Decoder → Normalizer → Encoder → Writer chain.
    Reader is optional for plugin-bound pipelines (data already in hand).
    """

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
        """Run pipeline with pre-fetched raw data (plugin-bound path)."""
        decoded  = await self.decoder.decode(raw)
        envelope = await self.normalizer.normalize(decoded, meta)
        encoded  = await self.encoder.encode(envelope)
        await self.writer.write(encoded, sink_config)
        log.info(
            "event=pipeline_completed envelope_id=%s protocol=%s",
            envelope.id, envelope.protocol,
        )
        return envelope

    async def run_with_reader(
        self,
        source_config: dict[str, Any],
        sink_config:   dict[str, Any],
    ) -> MessageEnvelope:
        """Run pipeline with Reader stage (ad-hoc / async-job path)."""
        if self.reader is None:
            raise ValueError("No Reader configured for this pipeline")
        raw = await self.reader.read(source_config)
        return await self.run(raw, source_config, sink_config)


class PipelineRegistry:
    """
    Holds all registered stage implementations.
    Plugins call register_* at on_startup().
    TransformRouter uses get_pipeline() to assemble ad-hoc pipelines.
    """

    def __init__(self) -> None:
        self._decoders:  dict[str, Decoder]    = {}
        self._encoders:  dict[str, Encoder]    = {}
        self._readers:   dict[str, Reader]     = {}
        self._writers:   dict[str, Writer]     = {}
        self._normalizer: Normalizer | None    = None

    # --- Registration ---

    def set_normalizer(self, normalizer: Normalizer) -> None:
        self._normalizer = normalizer

    def register_decoder(self, name: str, impl: Decoder) -> None:
        self._decoders[name] = impl
        log.debug("pipeline_registry decoder_registered name=%s", name)

    def register_encoder(self, name: str, impl: Encoder) -> None:
        self._encoders[name] = impl

    def register_reader(self, name: str, impl: Reader) -> None:
        self._readers[name] = impl

    def register_writer(self, name: str, impl: Writer) -> None:
        self._writers[name] = impl

    # --- Listing ---

    @property
    def stages(self) -> dict:
        return {
            "decoders": list(self._decoders),
            "encoders": list(self._encoders),
            "readers":  list(self._readers),
            "writers":  list(self._writers),
        }

    # --- Assembly (Phase 2 ad-hoc pipelines) ---

    def get_pipeline(
        self,
        decoder_name:  str,
        encoder_name:  str,
        writer_name:   str,
        reader_name:   str | None = None,
    ) -> TransformPipeline:
        if self._normalizer is None:
            raise RuntimeError("Normalizer not registered — call set_normalizer() at startup")
        return TransformPipeline(
            decoder=self._get(self._decoders, decoder_name, "decoder"),
            normalizer=self._normalizer,
            encoder=self._get(self._encoders, encoder_name, "encoder"),
            writer=self._get(self._writers, writer_name, "writer"),
            reader=self._get(self._readers, reader_name, "reader") if reader_name else None,
        )

    @staticmethod
    def _get(store: dict, name: str, kind: str):
        if name not in store:
            raise KeyError(f"{kind} '{name}' not registered in PipelineRegistry")
        return store[name]
