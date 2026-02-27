"""SFTP plugin request models."""
from pydantic import BaseModel, Field


class SFTPReceiveRequest(BaseModel):
    """Inject a file payload already fetched from SFTP."""
    payload:      dict
    source_ne:    str   = "unknown"
    domain:       str   = "PM"
    filename:     str   = "data.json"


class SFTPSimulateRequest(BaseModel):
    count:     int   = Field(1, ge=1, le=100)
    source_ne: str   = "sim-sftp-01"
    domain:    str   = "PM"
    decoder:   str   = "json"
