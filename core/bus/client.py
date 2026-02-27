"""NATS JetStream singleton client.

Holds one persistent connection per process lifetime.
Call connect() at app startup, drain() at shutdown.
"""

import logging

import nats
from nats.aio.client import Client as NATSClient
from nats.js import JetStreamContext

log = logging.getLogger(__name__)

_client: NATSClient | None = None
_js:     JetStreamContext | None = None


async def connect(url: str) -> NATSClient:
    global _client, _js
    _client = await nats.connect(
        url,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,   # retry forever
        error_cb=_on_error,
        disconnected_cb=_on_disconnect,
        reconnected_cb=_on_reconnect,
    )
    _js = _client.jetstream()
    log.info("nats_connected", extra={"url": url})
    return _client


async def drain() -> None:
    global _client
    if _client and _client.is_connected:
        await _client.drain()
        log.info("nats_drained")


def get_client() -> NATSClient:
    if not _client:
        raise RuntimeError("NATS client not initialised. Call bus.connect() at startup.")
    return _client


def get_js() -> JetStreamContext:
    if not _js:
        raise RuntimeError("JetStream context not initialised.")
    return _js


async def _on_error(exc: Exception) -> None:
    log.error("nats_error", extra={"error": str(exc)})


async def _on_disconnect() -> None:
    log.warning("nats_disconnected")


async def _on_reconnect() -> None:
    log.info("nats_reconnected")
