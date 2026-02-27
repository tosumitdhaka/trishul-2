from __future__ import annotations

import logging

import nats
from nats.aio.client import Client as NATSClient

log = logging.getLogger(__name__)

_client: NATSClient | None = None


async def connect(url: str) -> NATSClient:
    global _client

    async def _disconnected_cb():
        log.warning("event=nats_disconnected")

    async def _reconnected_cb():
        log.info("event=nats_reconnected")

    async def _error_cb(err):
        log.error("event=nats_error error=%s", err)

    _client = await nats.connect(
        url,
        disconnected_cb=_disconnected_cb,
        reconnected_cb=_reconnected_cb,
        error_cb=_error_cb,
        max_reconnect_attempts=-1,   # reconnect indefinitely
        reconnect_time_wait=2,
    )
    log.info("event=nats_connected url=%s", url)
    return _client


def get_nats_client() -> NATSClient:
    if _client is None or not _client.is_connected:
        raise RuntimeError("NATS client not initialised — call connect() first")
    return _client


async def drain() -> None:
    global _client
    if _client and _client.is_connected:
        await _client.drain()
        log.info("event=nats_drained")
    _client = None
