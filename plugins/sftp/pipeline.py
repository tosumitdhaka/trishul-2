"""SFTP pipeline assembly."""
from transformer.pipeline import TransformPipeline
from transformer.decoders.json import JSONDecoder
from transformer.normalizer import fcaps_normalizer
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter


def build_sftp_pipeline(nats_client, subject: str) -> TransformPipeline:
    return TransformPipeline(
        decoder    = JSONDecoder(),
        normalizer = fcaps_normalizer,
        encoder    = JSONEncoder(),
        writer     = NATSWriter(nats_client),
    )
