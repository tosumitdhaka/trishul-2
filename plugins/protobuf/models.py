"""Protobuf plugin request models."""
from pydantic import BaseModel, Field


class ProtobufReceiveRequest(BaseModel):
    payload:   dict
    schema_id: str | None = None
    source_ne: str        = "unknown"
    domain:    str        = "PM"


class ProtobufSimulateRequest(BaseModel):
    count:     int  = Field(1, ge=1, le=100)
    source_ne: str  = "sim-gnmi-01"
    domain:    str  = "PM"
