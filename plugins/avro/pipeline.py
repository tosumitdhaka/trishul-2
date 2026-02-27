"""Avro pipeline assembly."""
from transformer.pipeline import TransformPipeline
from transformer.decoders.avro import AvroDecoder
from transformer.decoders.json import JSONDecoder
from transformer.normalizer import fcaps_normalizer
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter


def build_avro_pipeline(nats_client, subject: str) -> TransformPipeline:
    # For dict payloads (pre-decoded or simulated), use JSONDecoder as passthrough
    return TransformPipeline(
        decoder    = JSONDecoder(),
        normalizer = fcaps_normalizer,
        encoder    = JSONEncoder(),
        writer     = NATSWriter(nats_client),
    )
