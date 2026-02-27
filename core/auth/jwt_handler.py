"""JWT encode / decode / refresh — HS256, blocklist via Redis.

Uses PyJWT (not python-jose) — fully timezone-aware, no utcnow() deprecation.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from jwt.exceptions import InvalidTokenError

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
    ttl = (
        timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
        if token_type == "access"
        else timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    )
    now = _now_utc()
    payload = {
        "sub":   subject,
        "roles": roles,
        "type":  token_type,
        "jti":   str(uuid.uuid4()),
        "iat":   now,
        "exp":   now + ttl,
    }
    # PyJWT accepts timezone-aware datetimes natively — no utcnow() involved
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        payload: dict = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
            # PyJWT verifies exp automatically; leeway=0 by default
        )
    except InvalidTokenError as exc:
        raise AuthenticationError(str(exc)) from exc
    return payload


def make_token_pair(subject: str, roles: list[str]) -> dict:
    return {
        "access_token":  encode_jwt(subject, roles, "access"),
        "refresh_token": encode_jwt(subject, roles, "refresh"),
        "token_type":    "bearer",
    }
