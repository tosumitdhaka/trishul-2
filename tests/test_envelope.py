"""Tests for FCAPSNormalizer."""
import pytest
from datetime import datetime, timezone
from transformer.normalizer import FCAPSNormalizer
from core.models.envelope import FCAPSDomain, Direction, Severity

normalizer = FCAPSNormalizer()


@pytest.mark.asyncio
async def test_normalize_fm_event():
    decoded = {"message": "linkDown", "severity": "CRITICAL", "source_ne": "router-01"}
    meta = {
        "domain":    "FM",
        "protocol":  "webhook",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await normalizer.normalize(decoded, meta)
    assert envelope.domain    == FCAPSDomain.FM
    assert envelope.severity  == Severity.CRITICAL
    assert envelope.source_ne == "router-01"
    assert envelope.direction == Direction.INBOUND


@pytest.mark.asyncio
async def test_normalize_pm_event():
    decoded = {"value": 42.5, "metric_name": "ifInOctets"}
    meta = {
        "domain":    "PM",
        "protocol":  "snmp",
        "source_ne": "router-02",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await normalizer.normalize(decoded, meta)
    assert envelope.domain              == FCAPSDomain.PM
    assert envelope.severity            is None
    assert envelope.source_ne           == "router-02"
    assert envelope.normalized["value"] == 42.5


@pytest.mark.asyncio
async def test_normalize_simulated():
    decoded = {"message": "test event"}
    meta = {
        "domain":    "FM",
        "protocol":  "webhook",
        "direction": "simulated",
        "source_ne": "sim-ne-01",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await normalizer.normalize(decoded, meta)
    assert envelope.direction == Direction.SIMULATED


@pytest.mark.asyncio
async def test_normalize_generates_uuid_if_no_envelope_id():
    decoded = {"message": "no id passed"}
    meta = {
        "domain":    "LOG",
        "protocol":  "webhook",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await normalizer.normalize(decoded, meta)
    assert envelope.id is not None
    assert len(envelope.id) == 36  # UUID4 length


@pytest.mark.asyncio
async def test_normalize_uses_meta_source_ne_over_decoded():
    decoded  = {"source_ne": "from-decoded"}
    meta = {
        "domain":    "FM",
        "protocol":  "webhook",
        "source_ne": "from-meta",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await normalizer.normalize(decoded, meta)
    assert envelope.source_ne == "from-meta"  # meta takes priority
