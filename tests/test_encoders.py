"""Unit tests for all Transformer encoders."""
import json
import pytest
from datetime import datetime, timezone
from core.models.envelope import MessageEnvelope, FCAPSDomain, Direction, Severity
from transformer.encoders.json import JSONEncoder
from transformer.encoders.csv import CSVEncoder
from transformer.encoders.protobuf import ProtobufEncoder


def _make_envelope(**kwargs) -> MessageEnvelope:
    defaults = dict(
        domain      = FCAPSDomain.FM,
        protocol    = "webhook",
        source_ne   = "router-01",
        direction   = Direction.INBOUND,
        severity    = Severity.MAJOR,
        raw_payload = {},
        normalized  = {"message": "linkDown", "value": 42.5},
        timestamp   = datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return MessageEnvelope(**defaults)


@pytest.mark.asyncio
async def test_json_encoder_returns_bytes():
    enc    = JSONEncoder()
    env    = _make_envelope()
    result = await enc.encode(env)
    assert isinstance(result, bytes)
    data = json.loads(result)
    assert data["domain"]    == "FM"
    assert data["source_ne"] == "router-01"


@pytest.mark.asyncio
async def test_json_encoder_normalized_present():
    enc    = JSONEncoder()
    env    = _make_envelope(normalized={"key": "val", "count": 7})
    result = await enc.encode(env)
    data   = json.loads(result)
    assert data["normalized"]["count"] == 7


@pytest.mark.asyncio
async def test_csv_encoder_returns_bytes():
    enc    = CSVEncoder()
    env    = _make_envelope(normalized={"source_ne": "r1", "value": "99"})
    result = await enc.encode(env)
    assert isinstance(result, bytes)
    lines  = result.decode().strip().splitlines()
    assert lines[0] == "source_ne,value"     # header
    assert lines[1] == "r1,99"               # data row


@pytest.mark.asyncio
async def test_csv_encoder_header_matches_keys():
    enc  = CSVEncoder()
    env  = _make_envelope(normalized={"a": "1", "b": "2", "c": "3"})
    out  = (await enc.encode(env)).decode()
    lines = out.strip().splitlines()
    assert lines[0] == "a,b,c"


@pytest.mark.asyncio
async def test_protobuf_encoder_fallback_json():
    enc    = ProtobufEncoder()
    env    = _make_envelope()
    result = await enc.encode(env)
    # Phase 2 scaffold falls back to JSON bytes
    assert isinstance(result, bytes)
    data = json.loads(result)
    assert data["protocol"] == "webhook"
