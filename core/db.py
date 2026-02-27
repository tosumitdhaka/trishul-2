"""SQLite database setup via SQLModel + seed default admin."""
from contextlib import contextmanager
from typing import Generator

import bcrypt
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


def hash_password(plain: str) -> str:
    """bcrypt hash — returns a str for SQLite storage."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time bcrypt verify."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _seed_admin(engine) -> None:
    """Create default admin user on first boot if not present."""
    import json
    from core.auth.models import User

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == "admin")).first()
        if existing:
            # Re-seed if hash is from broken passlib run (starts with $2b$ but
            # was never actually stored — seeding always failed before this fix)
            return
        admin = User(
            id        = "admin-seed-001",
            username  = "admin",
            hashed_pw = hash_password("trishul"),
            roles     = json.dumps(["admin"]),
            is_active = True,
        )
        session.add(admin)
        session.commit()

        import structlog
        structlog.get_logger().info("admin_user_seeded", username="admin")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
