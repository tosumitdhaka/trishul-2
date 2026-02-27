"""Schema Registry — SQLite-backed storage for Avro and Protobuf schemas."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from core.config.settings import get_settings


class SchemaRecord(SQLModel, table=True):
    __tablename__ = "schemas"

    id:         str      = Field(primary_key=True)
    name:       str      = Field(index=True)
    format:     str                          # 'avro' | 'protobuf'
    version:    str
    content:    str                          # JSON schema or .proto text
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SchemaRegistry:
    def __init__(self, db_path: str | None = None) -> None:
        path    = db_path or get_settings().SQLITE_PATH
        self._engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self._engine)

    def create(self, schema_id: str, name: str, fmt: str, version: str, content: str) -> SchemaRecord:
        record = SchemaRecord(
            id=schema_id, name=name, format=fmt,
            version=version, content=content,
        )
        with Session(self._engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
        return record

    def get(self, schema_id: str) -> Optional[SchemaRecord]:
        with Session(self._engine) as session:
            return session.get(SchemaRecord, schema_id)

    def list_all(self) -> list[SchemaRecord]:
        with Session(self._engine) as session:
            return list(session.exec(select(SchemaRecord)).all())

    def delete(self, schema_id: str) -> bool:
        with Session(self._engine) as session:
            record = session.get(SchemaRecord, schema_id)
            if not record:
                return False
            session.delete(record)
            session.commit()
        return True

    async def get_parsed_schema(self, fmt: str) -> dict | None:
        """Return first registered schema of given format, parsed as dict (for fastavro)."""
        with Session(self._engine) as session:
            results = session.exec(
                select(SchemaRecord).where(SchemaRecord.format == fmt)
            ).first()
        if results:
            return json.loads(results.content)
        return None


# Module-level singleton
_registry: SchemaRegistry | None = None


def get_schema_registry() -> SchemaRegistry:
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry
