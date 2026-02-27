"""Abstract base classes for all storage adapters."""
from abc import ABC, abstractmethod
from core.models.envelope import MessageEnvelope


class MetricsStore(ABC):
    """Stores and queries Performance Management (PM) time-series data."""

    @abstractmethod
    async def write_pm(self, envelope: MessageEnvelope) -> None:
        """Write PM metrics from a normalized MessageEnvelope."""
        ...

    @abstractmethod
    async def query_pm(
        self,
        source_ne: str,
        start: str,
        end: str,
        metric_name: str | None = None,
        limit: int = 500,
    ) -> list[dict]:
        """Query PM metrics. start/end are ISO 8601 strings or relative like '-1h'."""
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...


class EventStore(ABC):
    """Stores and queries Fault Management (FM) alarms and LOG entries."""

    @abstractmethod
    async def write_fm(self, envelope: MessageEnvelope) -> None:
        """Write FM alarm from a normalized MessageEnvelope."""
        ...

    @abstractmethod
    async def write_log(self, envelope: MessageEnvelope) -> None:
        """Write LOG entry from a normalized MessageEnvelope."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        domain: str,
        start: str,
        end: str,
        limit: int = 100,
    ) -> list[dict]:
        """Full-text search over FM/LOG entries using LogsQL syntax."""
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...
