"""JWT encode / decode / refresh — HS256, blocklist via Redis."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt

from core.config.settings import get_settings
from core.exceptions import AuthenticationError

ALGORITHM = "HS256"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def encode_jwt(
    subject: str,
    roles: list[str],
    token_type: Literal["access", "refresh"],
) -> str:
    settings = get_settings()
    if token_type == "access":
        ttl = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    else:
        ttl = timedelta(days=settings.JWT_REFRESH_TTL_DAYS)

    now = _now_utc()
    payload = {
        "sub":   subject,
        "roles": roles,
        "type":  token_type,
        "jti":   str(uuid.uuid4()),
        "iat":   now,
        "exp":   now + ttl,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError(str(exc)) from exc
    return payload


def make_token_pair(subject: str, roles: list[str]) -> dict:
    return {
        "access_token":  encode_jwt(subject, roles, "access"),
        "refresh_token": encode_jwt(subject, roles, "refresh"),
        "token_type":    "bearer",
    }
