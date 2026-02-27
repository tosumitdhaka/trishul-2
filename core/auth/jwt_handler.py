from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from core.config.settings import get_settings
from core.exceptions import AuthenticationError

_ALGORITHM = "HS256"


def _settings():
    return get_settings()


def encode_access_token(user_id: str, username: str, roles: list[str]) -> str:
    s = _settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub":  user_id,
        "usr":  username,
        "roles": roles,
        "type": "access",
        "jti":  str(uuid.uuid4()),
        "iat":  now,
        "exp":  now + timedelta(minutes=s.jwt_access_ttl_minutes),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=_ALGORITHM)


def encode_refresh_token(user_id: str) -> str:
    s = _settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub":  user_id,
        "type": "refresh",
        "jti":  str(uuid.uuid4()),
        "iat":  now,
        "exp":  now + timedelta(days=s.jwt_refresh_ttl_days),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    s = _settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError(f"Invalid or expired token: {exc}") from exc
    return payload
