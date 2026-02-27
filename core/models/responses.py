from __future__ import annotations

from typing import Generic, TypeVar

from .base import TrishulBaseModel

T = TypeVar("T")


class TrishulResponse(TrishulBaseModel, Generic[T]):
    """Uniform response wrapper for all synchronous endpoints."""
    success:  bool
    data:     T | None   = None
    error:    str | None = None
    trace_id: str | None = None

    @classmethod
    def ok(cls, data: T, trace_id: str | None = None) -> "TrishulResponse[T]":
        return cls(success=True, data=data, trace_id=trace_id)

    @classmethod
    def fail(cls, error: str, trace_id: str | None = None) -> "TrishulResponse[T]":
        return cls(success=False, error=error, trace_id=trace_id)


class AcceptedResponse(TrishulBaseModel):
    """202 Accepted — for all async (NATS-queued) ingest endpoints."""
    envelope_id: str
    status:      str = "accepted"
    message:     str = "Message queued for processing"
