"""SimulatorBase — shared synthetic data generator used by all plugins."""
from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class SimulatorBase(ABC):
    """Base class for all protocol simulators.
    Subclasses implement _generate_one() to produce a single synthetic message.
    """

    @abstractmethod
    def _generate_one(self, index: int, **kwargs) -> dict:
        """Return a single synthetic decoded dict."""
        ...

    def generate_batch(self, count: int = 1, **kwargs) -> list[dict]:
        return [self._generate_one(i, **kwargs) for i in range(count)]

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())
