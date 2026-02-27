"""Shared pytest fixtures for all tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET",    "test-secret-that-is-long-enough-32chars")
    monkeypatch.setenv("INFLUX_URL",    "http://localhost:8086")
    monkeypatch.setenv("INFLUX_TOKEN",  "test-token")
    monkeypatch.setenv("VICTORIA_URL",  "http://localhost:9428")
    monkeypatch.setenv("NATS_URL",      "nats://localhost:4222")
    monkeypatch.setenv("REDIS_URL",     "redis://localhost:6379")


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.ping.return_value  = True
    r.get.return_value   = None
    r.set.return_value   = True
    r.exists.return_value = 0
    r.incr.return_value  = 1
    r.expire.return_value = True
    r.setex.return_value = True
    return r


@pytest.fixture
def mock_nats():
    n = MagicMock()
    n.nc.is_connected = True
    n.js.publish      = AsyncMock()
    n.drain           = AsyncMock()
    return n


@pytest.fixture
def mock_metrics_store():
    s = AsyncMock()
    s.health.return_value    = True
    s.write_pm.return_value  = None
    s.query_pm.return_value  = []
    return s


@pytest.fixture
def mock_event_store():
    s = AsyncMock()
    s.health.return_value    = True
    s.write_fm.return_value  = None
    s.write_log.return_value = None
    s.search.return_value    = []
    return s
