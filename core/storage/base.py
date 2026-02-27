from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from core.models.envelope import MessageEnvelope


class MetricsStore(ABC):
    """Abstract interface for Performance Management (PM) time-series writes/reads."""

    @abstractmethod
    async def write_pm(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def query_pm(
        self,
        source_ne: str,
        start: datetime,
        end: datetime,
        metric_name: str | None = None,
    ) -> list[dict]: ...

    @abstractmethod
    async def health(self) -> bool: ...


class EventStore(ABC):
    """Abstract interface for FM alarms and LOG entries."""

    @abstractmethod
    async def write_fm(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def write_log(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def search(
        self,
        query: str,
        domain: str,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[dict]: ...

    @abstractmethod
    async def health(self) -> bool: ...
