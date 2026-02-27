from typing import Generic, TypeVar

from core.models.base import TrishulBaseModel

T = TypeVar("T")


class TrishulResponse(TrishulBaseModel, Generic[T]):
    """Uniform response wrapper for all synchronous API endpoints.

    Every 200/201/4xx/5xx response uses this shape.
    Never return bare dicts or naked HTTPExceptions.
    """

    success:  bool
    data:     T | None    = None
    error:    str | None  = None
    trace_id: str | None  = None

    @classmethod
    def ok(cls, data: T, trace_id: str | None = None) -> "TrishulResponse[T]":
        return cls(success=True, data=data, trace_id=trace_id)

    @classmethod
    def fail(cls, error: str, trace_id: str | None = None) -> "TrishulResponse[None]":
        return cls(success=False, error=error, trace_id=trace_id)


class AcceptedResponse(TrishulBaseModel):
    """202 response for async ingest endpoints (POST /receive)."""

    envelope_id: str
    status:      str = "accepted"
    message:     str = "Message queued for processing"
