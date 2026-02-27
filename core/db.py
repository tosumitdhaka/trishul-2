"""SQLite database setup via SQLModel + seed default admin."""
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine, select

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
        _seed_admin(_engine)
    return _engine


def _seed_admin(engine) -> None:
    """Create default admin user on first boot if not present."""
    import json
    from passlib.context import CryptContext
    from core.auth.models import User

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == "admin")).first()
        if existing:
            return
        admin = User(
            id         = "admin-seed-001",
            username   = "admin",
            hashed_pw  = pwd_ctx.hash("trishul"),
            roles      = json.dumps(["admin"]),
            is_active  = True,
        )
        session.add(admin)
        session.commit()

        import structlog
        structlog.get_logger().info("admin_user_seeded", username="admin")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
