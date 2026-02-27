from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id:         str              = Field(primary_key=True)
    username:   str              = Field(unique=True, index=True)
    hashed_pw:  str
    roles:      str              = Field(description="JSON array, e.g. ['admin']")
    is_active:  bool             = Field(default=True)
    created_at: datetime         = Field(default_factory=datetime.utcnow)


class APIKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id:          str              = Field(primary_key=True)
    client_id:   str              = Field(index=True)
    key_hash:    str              = Field(unique=True, description="SHA-256 of raw key")
    roles:       str              = Field(description="JSON array")
    rate_limit:  int              = Field(default=60)
    description: Optional[str]   = Field(default=None)
    is_active:   bool             = Field(default=True)
    created_at:  datetime         = Field(default_factory=datetime.utcnow)
    last_used:   Optional[datetime] = Field(default=None)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id:         str           = Field(primary_key=True)
    user_id:    Optional[str] = Field(default=None)
    action:     str           = Field(description="login|logout|api_key_created|plugin_loaded")
    detail:     Optional[str] = Field(default=None, description="JSON")
    ip_address: Optional[str] = Field(default=None)
    trace_id:   Optional[str] = Field(default=None)
    created_at: datetime      = Field(default_factory=datetime.utcnow)
