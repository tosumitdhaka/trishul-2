"""NATS singleton client with auto-reconnect."""
from __future__ import annotations

import nats
from nats.aio.client import Client as NATSClient

_client: NATSClient | None = None


class TrishulNATSClient:
    """Thin wrapper around nats.py client — singleton pattern."""

    def __init__(self) -> None:
        self._nc: NATSClient | None = None

    async def connect(self, url: str) -> None:
        self._nc = await nats.connect(
            url,
            reconnect_time_wait=2,
            max_reconnect_attempts=-1,     # reconnect forever
            error_cb=self._on_error,
            disconnected_cb=self._on_disconnect,
            reconnected_cb=self._on_reconnect,
        )

    @property
    def js(self):
        """JetStream context."""
        if self._nc is None:
            raise RuntimeError("NATS not connected")
        return self._nc.jetstream()

    @property
    def nc(self) -> NATSClient:
        if self._nc is None:
            raise RuntimeError("NATS not connected")
        return self._nc

    async def drain(self) -> None:
        if self._nc and not self._nc.is_closed:
            await self._nc.drain()

    @staticmethod
    async def _on_error(exc: Exception) -> None:
        import structlog
        structlog.get_logger().error("nats_error", error=str(exc))

    @staticmethod
    async def _on_disconnect() -> None:
        import structlog
        structlog.get_logger().warning("nats_disconnected")

    @staticmethod
    async def _on_reconnect() -> None:
        import structlog
        structlog.get_logger().info("nats_reconnected")


_instance: TrishulNATSClient | None = None


def get_nats_client() -> TrishulNATSClient:
    global _instance
    if _instance is None:
        _instance = TrishulNATSClient()
    return _instance
