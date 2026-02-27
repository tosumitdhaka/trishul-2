from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.auth.apikey_store import is_blocklisted, lookup_api_key
from core.auth.jwt_handler import decode_token
from core.exceptions import AuthenticationError, AuthorizationError

PUBLIC_PATHS = frozenset([
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
])


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header: str | None = request.headers.get("Authorization")
        api_key_header: str | None = request.headers.get("X-API-Key")
        redis = request.app.state.redis

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
            except AuthenticationError:
                return _unauthorized("Invalid or expired token")

            jti = payload.get("jti", "")
            if await is_blocklisted(redis, jti):
                return _unauthorized("Token has been revoked")

            request.state.user = {
                "id":        payload["sub"],
                "username":  payload.get("usr", ""),
                "roles":     payload.get("roles", []),
                "auth_type": "jwt",
                "jti":       jti,
                "exp":       payload.get("exp"),
            }

        elif api_key_header:
            client = await lookup_api_key(redis, api_key_header)
            if client is None:
                return _unauthorized("Invalid API key")
            request.state.user = {
                "id":        client["client_id"],
                "username":  client["client_id"],
                "roles":     client["roles"],
                "auth_type": "api_key",
            }
        else:
            return _unauthorized("Authentication required")

        return await call_next(request)


def require_role(*roles: str):
    """FastAPI dependency — raises 403 if user lacks required role."""
    from fastapi import Depends
    from core.dependencies import current_user

    async def _check(user: dict = Depends(current_user)):
        user_roles: list[str] = user.get("roles", [])
        if not any(r in user_roles for r in ("admin", *roles)):
            raise AuthorizationError(f"Requires one of roles: {list(roles)}")
        return user

    return Depends(_check)


def _unauthorized(detail: str) -> Response:
    body = json.dumps({"success": False, "error": detail, "data": None})
    return Response(content=body, status_code=401, media_type="application/json")
