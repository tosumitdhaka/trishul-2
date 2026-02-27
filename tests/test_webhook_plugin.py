"""Tests for Webhook plugin: receive, simulate, status."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from plugins.webhook.router import router


@pytest.fixture
def app(mock_redis, mock_nats):
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1/webhook")
    _app.state.redis = mock_redis
    _app.state.nats  = mock_nats
    return _app


def test_receive_returns_202(app):
    with TestClient(app) as client:
        resp = client.post("/api/v1/webhook/receive", json={
            "source_ne": "router-01",
            "domain":    "FM",
            "severity":  "MAJOR",
            "message":   "linkDown on router-01",
            "data":      {},
        })
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "accepted"
    assert "envelope_id" in data


def test_receive_publishes_to_nats(app, mock_nats):
    with TestClient(app) as client:
        client.post("/api/v1/webhook/receive", json={
            "source_ne": "ne-01",
            "domain":    "FM",
            "data":      {},
        })
    mock_nats.js.publish.assert_called_once()
    call_args = mock_nats.js.publish.call_args
    assert call_args[0][0] == "fcaps.ingest.webhook"


def test_simulate_returns_envelope_ids(app):
    with TestClient(app) as client:
        resp = client.post("/api/v1/webhook/simulate", json={
            "count":     3,
            "domain":    "FM",
            "severity":  "MAJOR",
            "source_ne": "sim-ne-01",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["sent"] == 3
    assert len(data["data"]["envelope_ids"]) == 3


def test_status_not_found(app):
    with TestClient(app) as client:
        resp = client.get("/api/v1/webhook/status/nonexistent-id")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "not_found"
