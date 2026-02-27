from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

from fastapi import WebSocket

log = logging.getLogger(__name__)

_connections: Set[WebSocket] = set()


async def register(ws: WebSocket) -> None:
    await ws.accept()
    _connections.add(ws)
    log.info("event=ws_client_connected total=%d", len(_connections))


async def unregister(ws: WebSocket) -> None:
    _connections.discard(ws)
    log.info("event=ws_client_disconnected total=%d", len(_connections))


async def broadcast(message: dict) -> None:
    if not _connections:
        return
    payload = json.dumps(message)
    dead: Set[WebSocket] = set()
    for ws in list(_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _connections -= dead


async def start_broadcaster(nc) -> None:
    """
    Subscribe to fcaps.done.> and fan-out to all connected WebSocket clients.
    Phase 4 will expose the actual WS endpoint — this wires the NATS side.
    """
    js = nc.jetstream()

    async def _handler(msg):
        try:
            data = json.loads(msg.data.decode())
            await broadcast(data)
            await msg.ack()
        except Exception as exc:
            log.error("event=broadcaster_error error=%s", exc)
            await msg.nak()

    await js.subscribe("fcaps.done.>", durable="ws-broadcaster", cb=_handler)
    log.info("event=ws_broadcaster_started")
