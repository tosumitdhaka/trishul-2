"""Storage adapter ABCs.

All route handlers and transformer writers use these interfaces.
Never import InfluxDB or VictoriaLogs clients directly in handlers.
"""

from abc import ABC, abstractmethod

from core.models.envelope import MessageEnvelope


class MetricsStore(ABC):
    """Time-series storage for PM metrics (InfluxDB in lab/prod)."""

    @abstractmethod
    async def write_pm(self, envelope: MessageEnvelope) -> None:
        """Write a PM envelope as an InfluxDB line protocol point."""

    @abstractmethod
    async def query_pm(
        self,
        source_ne: str,
        start: str,
        end: str,
        metric_name: str | None = None,
    ) -> list[dict]:
        """Query PM metrics. start/end are InfluxDB duration strings (e.g. '-1h', 'now()')."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the storage backend is reachable."""


class EventStore(ABC):
    """Log/event storage for FM alarms and LOG entries (VictoriaLogs in lab/prod)."""

    @abstractmethod
    async def write_fm(self, envelope: MessageEnvelope) -> None:
        """Write an FM alarm envelope to VictoriaLogs."""

    @abstractmethod
    async def write_log(self, envelope: MessageEnvelope) -> None:
        """Write a LOG entry envelope to VictoriaLogs."""

    @abstractmethod
    async def search(
        self,
        query: str,
        domain: str,
        start: str,
        end: str,
        limit: int = 100,
    ) -> list[dict]:
        """Search using LogsQL syntax. domain filters the _stream field."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the storage backend is reachable."""
