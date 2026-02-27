"""SQLModel table definitions for auth: User, APIKey, AuditLog."""
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id:         str      = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username:   str      = Field(unique=True, index=True, max_length=64)
    hashed_pw:  str
    roles:      str                          # JSON array string: '["admin"]'
    is_active:  bool     = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class APIKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id:          str           = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    client_id:   str           = Field(index=True)
    key_hash:    str           = Field(unique=True)      # SHA-256, never raw
    roles:       str                                     # JSON array string
    rate_limit:  int           = 60
    description: Optional[str] = None
    is_active:   bool          = True
    created_at:  datetime      = Field(default_factory=datetime.utcnow)
    last_used:   Optional[datetime] = None


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id:         str           = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id:    Optional[str] = None
    action:     str                          # login | logout | api_key_created | plugin_loaded
    detail:     Optional[str] = None         # JSON string
    ip_address: Optional[str] = None
    trace_id:   Optional[str] = None
    created_at: datetime      = Field(default_factory=datetime.utcnow)
