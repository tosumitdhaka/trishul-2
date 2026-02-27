"""Protobuf pipeline assembly."""
from transformer.pipeline import TransformPipeline
from transformer.decoders.protobuf import ProtobufDecoder
from transformer.normalizer import fcaps_normalizer
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter


def build_protobuf_pipeline(nats_client, subject: str) -> TransformPipeline:
    return TransformPipeline(
        decoder    = ProtobufDecoder(),
        normalizer = fcaps_normalizer,
        encoder    = JSONEncoder(),
        writer     = NATSWriter(nats_client),
    )
