"""WebSocket event broadcaster — NATS fcaps.done.> → connected browsers."""
from __future__ import annotations
import json
import asyncio
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

log = structlog.get_logger(__name__)
router = APIRouter(tags=["ws"])


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        log.info("ws_client_connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        log.info("ws_client_disconnected", total=len(self._connections))

    async def broadcast(self, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """Browser connects here; receives all fcaps.done.> envelopes as JSON."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — clients are receive-only for now
            await asyncio.sleep(30)
            await websocket.send_text('{"type":"ping"}')
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def broadcast_envelope(envelope_dict: dict) -> None:
    """Called by NotificationService whenever a fcaps.done.* message arrives."""
    await manager.broadcast(json.dumps(envelope_dict))
