from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import TrishulBaseModel


class FCAPSDomain(str, Enum):
    FM  = "FM"    # Fault Management
    PM  = "PM"    # Performance Management
    LOG = "LOG"   # Generic log


class Direction(str, Enum):
    INBOUND   = "inbound"
    OUTBOUND  = "outbound"
    SIMULATED = "simulated"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR    = "MAJOR"
    MINOR    = "MINOR"
    WARNING  = "WARNING"
    CLEARED  = "CLEARED"


class MessageEnvelope(TrishulBaseModel):
    id:           str          = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_ver:   str          = Field(default="1.0")
    timestamp:    datetime     = Field(default_factory=lambda: datetime.now(timezone.utc))
    domain:       FCAPSDomain
    protocol:     str          = Field(..., description="snmp|ves|protobuf|avro|webhook|sftp")
    source_ne:    str          = Field(..., description="Network Element identifier")
    direction:    Direction    = Field(default=Direction.INBOUND)
    severity:     Severity | None = Field(default=None, description="Required for FM domain")
    raw_payload:  dict[str, Any] = Field(default_factory=dict)
    normalized:   dict[str, Any] = Field(default_factory=dict)
    tags:         list[str]    = Field(default_factory=list)
    trace_id:     str | None   = Field(default=None)

    @field_validator("severity", mode="before")
    @classmethod
    def coerce_severity(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v
