"""Tests for core models: MessageEnvelope, TrishulResponse, AcceptedResponse."""
import pytest
from datetime import datetime, timezone
from core.models.envelope import MessageEnvelope, FCAPSDomain, Direction, Severity
from core.models.responses import TrishulResponse, AcceptedResponse, ok, err, accepted


def test_envelope_defaults():
    env = MessageEnvelope(
        domain=FCAPSDomain.FM,
        protocol="webhook",
        source_ne="router-01",
        direction=Direction.INBOUND,
        raw_payload={"key": "val"},
        normalized={},
    )
    assert env.id is not None
    assert env.schema_ver == "1.0"
    assert env.domain == FCAPSDomain.FM
    assert env.direction == Direction.INBOUND
    assert env.severity is None


def test_envelope_severity_fm():
    env = MessageEnvelope(
        domain=FCAPSDomain.FM,
        protocol="snmp",
        source_ne="ne-01",
        direction=Direction.INBOUND,
        severity=Severity.CRITICAL,
        raw_payload={},
        normalized={},
    )
    assert env.severity == Severity.CRITICAL


def test_envelope_serialization():
    env = MessageEnvelope(
        domain=FCAPSDomain.PM,
        protocol="webhook",
        source_ne="ne-02",
        direction=Direction.SIMULATED,
        raw_payload={},
        normalized={"value": 42.0},
    )
    data = env.model_dump()
    assert data["domain"] == "PM"
    assert data["normalized"]["value"] == 42.0


def test_trishul_response_ok():
    r = ok({"key": "value"}, trace_id="abc")
    assert r.success is True
    assert r.data == {"key": "value"}
    assert r.error is None
    assert r.trace_id == "abc"


def test_trishul_response_err():
    r = err("Something failed", trace_id="xyz")
    assert r.success is False
    assert r.error == "Something failed"
    assert r.data is None


def test_accepted_response():
    r = accepted("uuid-123")
    assert r.envelope_id == "uuid-123"
    assert r.status == "accepted"
