"""Tests for TransformPipeline and PipelineRegistry assembly."""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from transformer.pipeline import (
    TransformPipeline, PipelineRegistry, PipelineJobConfig,
    StageConfig, NormalizerConfig,
)
from transformer.normalizer import FCAPSNormalizer
from transformer.decoders.json import JSONDecoder
from transformer.encoders.json import JSONEncoder
from transformer.writers.nats import NATSWriter
from core.models.envelope import FCAPSDomain, Direction


@pytest.fixture
def mock_nats():
    n = object.__new__(object.__class__)
    import types
    n = types.SimpleNamespace()
    n.js = types.SimpleNamespace()
    n.js.publish = AsyncMock()
    return n


@pytest.mark.asyncio
async def test_pipeline_run_end_to_end(mock_nats):
    pipeline = TransformPipeline(
        decoder    = JSONDecoder(),
        normalizer = FCAPSNormalizer(),
        encoder    = JSONEncoder(),
        writer     = NATSWriter(mock_nats),
    )
    raw  = b'{"message": "linkDown", "severity": "MAJOR"}'
    meta = {
        "domain":    "FM",
        "protocol":  "webhook",
        "source_ne": "router-01",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await pipeline.run(raw, meta, {"subject": "fcaps.done.test"})
    assert envelope.domain    == FCAPSDomain.FM
    assert envelope.source_ne == "router-01"
    mock_nats.js.publish.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_registry_get_pipeline(mock_nats):
    registry = PipelineRegistry()
    registry.register_decoder("json",  JSONDecoder())
    registry.register_encoder("json",  JSONEncoder())
    registry.register_writer("nats",   NATSWriter(mock_nats))

    config = PipelineJobConfig(
        decoder    = StageConfig(type="json"),
        normalizer = NormalizerConfig(domain="FM", protocol="webhook", source_ne="ne-01"),
        encoder    = StageConfig(type="json"),
        writer     = StageConfig(type="nats", subject="fcaps.done.x"),
    )
    pipeline = registry.get_pipeline(config, FCAPSNormalizer())
    assert isinstance(pipeline.decoder, JSONDecoder)
    assert isinstance(pipeline.encoder, JSONEncoder)


def test_pipeline_registry_missing_stage_raises(mock_nats):
    registry = PipelineRegistry()
    registry.register_decoder("json", JSONDecoder())
    # No encoder or writer registered

    config = PipelineJobConfig(
        decoder    = StageConfig(type="json"),
        normalizer = NormalizerConfig(domain="FM", protocol="webhook", source_ne="ne-01"),
        encoder    = StageConfig(type="json"),
        writer     = StageConfig(type="nats"),
    )
    with pytest.raises(ValueError, match="Unregistered pipeline stages"):
        registry.get_pipeline(config, FCAPSNormalizer())


def test_pipeline_registry_list_stages(mock_nats):
    registry = PipelineRegistry()
    registry.register_decoder("json", JSONDecoder())
    registry.register_encoder("json", JSONEncoder())
    stages = registry.list_stages()
    assert "json" in stages["decoders"]
    assert "json" in stages["encoders"]
    assert stages["readers"] == []
