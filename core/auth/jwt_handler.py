"""JWT encode/decode helpers using python-jose.

Token types:
  access  — short-lived (default 15 min), used for API calls
  refresh — long-lived (default 7 days), used only to get new access tokens

Both tokens carry:
  sub  — user_id
  jti  — unique token ID (UUID) used for blocklist checks on logout
  type — "access" | "refresh"
  roles — list of role strings
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt

from core.config.settings import get_settings

ALGORITHM = "HS256"


class AuthenticationError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def encode_jwt(
    user_id: str,
    roles: list[str],
    token_type: Literal["access", "refresh"],
) -> str:
    settings = get_settings()
    if token_type == "access":
        expire = _now() + timedelta(minutes=settings.jwt_access_ttl_minutes)
    else:
        expire = _now() + timedelta(days=settings.jwt_refresh_ttl_days)

    payload = {
        "sub":   user_id,
        "jti":   str(uuid.uuid4()),
        "type":  token_type,
        "roles": roles,
        "exp":   expire,
        "iat":   _now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT. Raises AuthenticationError on any failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError(str(exc)) from exc
    return payload


def token_remaining_seconds(payload: dict) -> int:
    """Returns seconds until expiry. Used to set Redis blocklist TTL."""
    exp = payload.get("exp")
    if not exp:
        return 0
    remaining = int(exp - _now().timestamp())
    return max(remaining, 0)
