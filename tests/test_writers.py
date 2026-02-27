"""Unit tests for Transformer writers (all sinks mocked)."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from core.models.envelope import MessageEnvelope, FCAPSDomain, Direction, Severity
from transformer.writers.nats import NATSWriter
from transformer.writers.influxdb import InfluxDBWriter
from transformer.writers.victorialogs import VictoriaLogsWriter
from transformer.writers.webhook import WebhookWriter
from transformer.writers.csv import CSVWriter


def _envelope_bytes(domain="FM") -> bytes:
    env = MessageEnvelope(
        domain      = FCAPSDomain(domain),
        protocol    = "webhook",
        source_ne   = "router-01",
        direction   = Direction.INBOUND,
        severity    = Severity.MAJOR,
        raw_payload = {},
        normalized  = {"message": "test"},
        timestamp   = datetime.now(timezone.utc),
    )
    return env.model_dump_json().encode()


# ── NATSWriter ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nats_writer_publishes_to_subject():
    mock_nats = MagicMock()
    mock_nats.js.publish = AsyncMock()
    writer = NATSWriter(mock_nats)
    data   = b'{"key": "value"}'
    await writer.write(data, {"subject": "fcaps.done.test"})
    mock_nats.js.publish.assert_called_once_with("fcaps.done.test", data)


@pytest.mark.asyncio
async def test_nats_writer_dict_serialized():
    mock_nats = MagicMock()
    mock_nats.js.publish = AsyncMock()
    writer = NATSWriter(mock_nats)
    await writer.write({"key": "val"}, {"subject": "fcaps.done.x"})
    call_args = mock_nats.js.publish.call_args[0]
    assert json.loads(call_args[1]) == {"key": "val"}


# ── InfluxDBWriter ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_influxdb_writer_calls_write_pm():
    mock_store = AsyncMock()
    writer     = InfluxDBWriter(mock_store)
    await writer.write(_envelope_bytes("PM"), {})
    mock_store.write_pm.assert_called_once()


@pytest.mark.asyncio
async def test_influxdb_writer_accepts_dict():
    mock_store = AsyncMock()
    writer     = InfluxDBWriter(mock_store)
    env_dict   = json.loads(_envelope_bytes("PM").decode())
    await writer.write(env_dict, {})
    mock_store.write_pm.assert_called_once()


# ── VictoriaLogsWriter ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_victoria_writer_fm_calls_write_fm():
    mock_store = AsyncMock()
    writer     = VictoriaLogsWriter(mock_store)
    await writer.write(_envelope_bytes("FM"), {})
    mock_store.write_fm.assert_called_once()


@pytest.mark.asyncio
async def test_victoria_writer_log_calls_write_log():
    mock_store = AsyncMock()
    writer     = VictoriaLogsWriter(mock_store)
    await writer.write(_envelope_bytes("LOG"), {})
    mock_store.write_log.assert_called_once()


# ── WebhookWriter ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_writer_posts_to_url(respx_mock=None):
    """Use httpx mock via patch."""
    import httpx
    writer  = WebhookWriter()
    payload = b'{"key": "value"}'

    with patch("transformer.writers.webhook.httpx.AsyncClient") as MockClient:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
        MockClient.return_value.__aexit__  = AsyncMock(return_value=False)
        MockClient.return_value.post       = AsyncMock(return_value=mock_resp)

        await writer.write(payload, {"url": "http://example.com/hook"})
        MockClient.return_value.post.assert_called_once()


# ── CSVWriter ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_csv_writer_creates_file(tmp_path):
    writer  = CSVWriter()
    outfile = tmp_path / "output.csv"
    await writer.write(b"col1,col2\nval1,val2", {"path": str(outfile)})
    assert outfile.exists()
    content = outfile.read_text()
    assert "col1,col2" in content


@pytest.mark.asyncio
async def test_csv_writer_appends_newline(tmp_path):
    writer  = CSVWriter()
    outfile = tmp_path / "out.csv"
    await writer.write(b"row1", {"path": str(outfile)})
    await writer.write(b"row2", {"path": str(outfile)})
    lines = outfile.read_text().splitlines()
    assert "row1" in lines
    assert "row2" in lines
