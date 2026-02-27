"""VES pipeline assembly."""
from transformer.pipeline import TransformPipeline
from transformer.decoders.ves import VESDecoder
from transformer.normalizer import fcaps_normalizer
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter


def build_ves_pipeline(nats_client, subject: str) -> TransformPipeline:
    return TransformPipeline(
        decoder    = VESDecoder(),
        normalizer = fcaps_normalizer,
        encoder    = JSONEncoder(),
        writer     = NATSWriter(nats_client),
    )
