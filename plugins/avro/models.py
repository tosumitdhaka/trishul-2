"""Avro plugin request models."""
from pydantic import BaseModel, Field


class AvroReceiveRequest(BaseModel):
    """Pre-decoded Avro record dict (SFTP pull or direct inject)."""
    payload:   dict
    schema_id: str | None = None
    source_ne: str        = "unknown"
    domain:    str        = "PM"


class AvroSimulateRequest(BaseModel):
    count:     int  = Field(1, ge=1, le=100)
    source_ne: str  = "sim-avro-01"
    domain:    str  = "PM"
