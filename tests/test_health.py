"""Tests for GET /health endpoint."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from core.health.router import router


@pytest.fixture
def app(mock_redis, mock_nats, mock_metrics_store, mock_event_store):
    _app = FastAPI()
    _app.include_router(router)
    _app.state.redis         = mock_redis
    _app.state.nats          = mock_nats
    _app.state.metrics_store = mock_metrics_store
    _app.state.event_store   = mock_event_store
    _app.state.plugin_registry = None
    return _app


def test_health_all_ok(app):
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "dependencies" in data


def test_health_redis_down(app, mock_redis):
    mock_redis.ping.side_effect = Exception("connection refused")
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "unhealthy"


def test_health_influx_down(app, mock_metrics_store):
    mock_metrics_store.health.return_value = False
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.json()["status"] == "degraded"
