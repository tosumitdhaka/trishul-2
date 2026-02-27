"""Uniform API response shapes — every endpoint returns TrishulResponse or AcceptedResponse."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class TrishulResponse(BaseModel, Generic[T]):
    success:  bool
    data:     Optional[T]   = None
    error:    Optional[str] = None
    trace_id: Optional[str] = None


class AcceptedResponse(BaseModel):
    envelope_id: str
    status:      str = "accepted"
    message:     str = "Message queued for processing"


def ok(data: T, trace_id: str | None = None) -> TrishulResponse[T]:
    return TrishulResponse(success=True, data=data, trace_id=trace_id)


def err(message: str, trace_id: str | None = None) -> TrishulResponse:
    return TrishulResponse(success=False, error=message, trace_id=trace_id)


def accepted(envelope_id: str) -> AcceptedResponse:
    return AcceptedResponse(envelope_id=envelope_id)
