"""Tests for VES plugin — simulator and decoder integration."""
import pytest
import json
from unittest.mock import AsyncMock
from plugins.ves.simulator import ves_simulator
from plugins.ves.pipeline import build_ves_pipeline
from transformer.decoders.ves import VESDecoder
from core.models.envelope import FCAPSDomain
import types
from datetime import datetime, timezone


@pytest.fixture
def mock_nats():
    n = types.SimpleNamespace()
    n.js = types.SimpleNamespace()
    n.js.publish = AsyncMock()
    return n


def test_ves_simulator_generates_fault():
    events = ves_simulator.generate_batch(count=3, domain="fault",
                                          severity="CRITICAL", source_ne="ems-01")
    assert len(events) == 3
    for e in events:
        hdr = e["event"]["commonEventHeader"]
        assert hdr["domain"] == "fault"
        assert hdr["sourceName"] == "ems-01"
        assert "faultFields" in e["event"]


def test_ves_simulator_generates_measurement():
    events = ves_simulator.generate_batch(count=1, domain="measurement",
                                          severity="MAJOR", source_ne="ems-02")
    assert "measurementFields" in events[0]["event"]


@pytest.mark.asyncio
async def test_ves_pipeline_run(mock_nats):
    pipeline = build_ves_pipeline(mock_nats, "fcaps.ingest.ves")
    ves_event = ves_simulator.generate_batch(
        count=1, domain="fault", severity="CRITICAL", source_ne="ems-01"
    )[0]
    meta = {
        "domain":    "FM",
        "protocol":  "ves",
        "source_ne": "ems-01",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await pipeline.run(ves_event, meta, {"subject": "fcaps.ingest.ves"})
    assert envelope.domain    == FCAPSDomain.FM
    assert envelope.source_ne == "ems-01"
    mock_nats.js.publish.assert_called_once()


@pytest.mark.asyncio
async def test_ves_simulate_endpoint():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    import types

    app   = FastAPI()
    nats  = types.SimpleNamespace()
    nats.js = types.SimpleNamespace()
    nats.js.publish = AsyncMock()
    app.state.nats  = nats
    app.state.redis = None

    from plugins.ves.router import router
    app.include_router(router, prefix="/api/v1")

    client = TestClient(app)
    resp   = client.post("/api/v1/ves/simulate",
                         json={"count": 2, "domain": "fault",
                               "severity": "CRITICAL", "source_ne": "ems-test"})
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 2
