"""SQLite database setup via SQLModel."""
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from core.config.settings import get_settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine  = create_engine(
            f"sqlite:///{settings.SQLITE_PATH}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(_engine)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
