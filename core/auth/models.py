import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Human user. Authenticates via username + password -> JWT."""

    __tablename__ = "users"

    id:         str      = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username:   str      = Field(unique=True, index=True)
    hashed_pw:  str
    roles:      str      = Field(default='["viewer"]', description="JSON array of role strings")
    is_active:  bool     = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class APIKey(SQLModel, table=True):
    """Machine client. Authenticates via X-API-Key header."""

    __tablename__ = "api_keys"

    id:          str      = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    client_id:   str      = Field(index=True)
    key_hash:    str      = Field(unique=True, description="SHA-256 of raw key. Never store raw.")
    roles:       str      = Field(default='["viewer"]', description="JSON array of role strings")
    rate_limit:  int      = Field(default=600)
    description: str      = Field(default="")
    is_active:   bool     = Field(default=True)
    created_at:  datetime = Field(default_factory=datetime.utcnow)
    last_used:   datetime | None = Field(default=None)


class AuditLog(SQLModel, table=True):
    """Append-only audit trail for auth events and admin actions."""

    __tablename__ = "audit_log"

    id:         str      = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id:    str | None = Field(default=None)
    action:     str      = Field(description="login | logout | api_key_created | plugin_loaded | ...")
    detail:     str | None = Field(default=None, description="JSON string")
    ip_address: str | None = Field(default=None)
    trace_id:   str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
