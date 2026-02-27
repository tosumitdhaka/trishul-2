"""Tests for FCAPSNormalizer."""
import pytest
import asyncio
from datetime import datetime, timezone
from transformer.normalizer import FCAPSNormalizer
from core.models.envelope import FCAPSDomain, Direction, Severity


normalizer = FCAPSNormalizer()


def test_normalize_fm_event():
    decoded = {"message": "linkDown", "severity": "CRITICAL", "source_ne": "router-01"}
    meta    = {"domain": "FM", "protocol": "webhook", "direction": "inbound",
               "timestamp": datetime.now(timezone.utc)}
    envelope = asyncio.get_event_loop().run_until_complete(
        normalizer.normalize(decoded, meta)
    )
    assert envelope.domain    == FCAPSDomain.FM
    assert envelope.severity  == Severity.CRITICAL
    assert envelope.source_ne == "router-01"
    assert envelope.direction == Direction.INBOUND


def test_normalize_pm_event():
    decoded = {"value": 42.5, "metric_name": "ifInOctets"}
    meta    = {"domain": "PM", "protocol": "snmp", "source_ne": "router-02",
               "direction": "inbound", "timestamp": datetime.now(timezone.utc)}
    envelope = asyncio.get_event_loop().run_until_complete(
        normalizer.normalize(decoded, meta)
    )
    assert envelope.domain    == FCAPSDomain.PM
    assert envelope.severity  is None
    assert envelope.source_ne == "router-02"
    assert envelope.normalized["value"] == 42.5


def test_normalize_simulated():
    decoded  = {"message": "test event"}
    meta     = {"domain": "FM", "protocol": "webhook", "direction": "simulated",
                "source_ne": "sim-ne-01", "timestamp": datetime.now(timezone.utc)}
    envelope = asyncio.get_event_loop().run_until_complete(
        normalizer.normalize(decoded, meta)
    )
    assert envelope.direction == Direction.SIMULATED
