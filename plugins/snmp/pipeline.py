"""SNMP pipeline assembly helpers."""
from transformer.pipeline import TransformPipeline
from transformer.decoders.snmp import SNMPDecoder
from transformer.normalizer import fcaps_normalizer
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter


def build_snmp_pipeline(nats_client, subject: str) -> TransformPipeline:
    return TransformPipeline(
        decoder    = SNMPDecoder(),
        normalizer = fcaps_normalizer,
        encoder    = JSONEncoder(),
        writer     = NATSWriter(nats_client),
    )
