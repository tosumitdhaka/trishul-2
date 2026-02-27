"""Tests for SNMP plugin — simulator and pipeline integration.
   Imports simulator + pipeline directly, NOT plugin.py.
"""
import pytest
from unittest.mock import AsyncMock
from plugins.snmp.simulator import snmp_simulator
from plugins.snmp.pipeline import build_snmp_pipeline
from core.models.envelope import FCAPSDomain
import types
from datetime import datetime, timezone


@pytest.fixture
def mock_nats():
    n = types.SimpleNamespace()
    n.js = types.SimpleNamespace()
    n.js.publish = AsyncMock()
    return n


def test_snmp_simulator_generates_batch():
    traps = snmp_simulator.generate_batch(count=5, trap_type="linkDown", source_ne="ne-01")
    assert len(traps) == 5
    for t in traps:
        assert t["agent_address"] == "ne-01"
        assert t["severity"] == "CRITICAL"


def test_snmp_simulator_linkup_cleared():
    traps = snmp_simulator.generate_batch(count=1, trap_type="linkUp", source_ne="ne-02")
    assert traps[0]["severity"] == "CLEARED"


@pytest.mark.asyncio
async def test_snmp_pipeline_run(mock_nats):
    pipeline = build_snmp_pipeline(mock_nats, "fcaps.ingest.snmp")
    trap = snmp_simulator.generate_batch(count=1, trap_type="linkDown", source_ne="router-01")[0]
    meta = {
        "domain":    "FM",
        "protocol":  "snmp",
        "source_ne": "router-01",
        "direction": "inbound",
        "timestamp": datetime.now(timezone.utc),
    }
    envelope = await pipeline.run(trap, meta, {"subject": "fcaps.ingest.snmp"})
    assert envelope.domain    == FCAPSDomain.FM
    assert envelope.source_ne == "router-01"
    mock_nats.js.publish.assert_called_once()


@pytest.mark.asyncio
async def test_snmp_simulate_endpoint():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    nats = types.SimpleNamespace()
    nats.js = types.SimpleNamespace()
    nats.js.publish = AsyncMock()
    app.state.nats  = nats
    app.state.redis = None

    from plugins.snmp.router import router
    app.include_router(router, prefix="/api/v1")

    client = TestClient(app)
    resp   = client.post("/api/v1/snmp/simulate",
                         json={"count": 3, "trap_type": "linkDown", "source_ne": "ne-test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["count"] == 3
    assert len(data["data"]["envelope_ids"]) == 3
