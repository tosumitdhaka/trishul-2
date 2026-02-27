import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from core.models.base import TrishulBaseModel


class FCAPSDomain(str, Enum):
    FM  = "FM"   # Fault Management
    PM  = "PM"   # Performance Management
    LOG = "LOG"  # General logs


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
    """The single unit of data that flows through the entire Trishul system.

    Every protocol plugin normalizes inbound data into a MessageEnvelope
    before publishing to NATS. The Transformer Engine consumes envelopes
    from NATS, enriches the `normalized` field, and writes to storage.
    """

    # Identity
    id:         str      = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_ver: str      = Field(default="1.0", description="Bump on breaking model changes")
    trace_id:   str | None = Field(default=None, description="Distributed trace ID")

    # Timing
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the envelope was created",
    )

    # Routing
    domain:    FCAPSDomain      = Field(..., description="FM | PM | LOG")
    protocol:  str              = Field(..., description="snmp | ves | protobuf | avro | webhook | sftp")
    source_ne: str              = Field(..., description="Network Element identifier")
    direction: Direction        = Field(default=Direction.INBOUND)

    # FM-specific
    severity: Severity | None   = Field(
        default=None,
        description="Required for FM domain; None for PM and LOG",
    )

    # Payload
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Original inbound data")
    normalized:  dict[str, Any] = Field(default_factory=dict, description="Protocol-agnostic decoded fields")
    tags:        list[str]      = Field(default_factory=list)

    @field_validator("severity")
    @classmethod
    def severity_required_for_fm(cls, v: Severity | None, info: Any) -> Severity | None:
        domain = info.data.get("domain")
        if domain == FCAPSDomain.FM and v is None:
            raise ValueError("severity is required when domain=FM")
        return v
