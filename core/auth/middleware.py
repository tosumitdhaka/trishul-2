"""AuthMiddleware: JWT + API Key validation, RBAC check, blocklist enforcement."""
import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.auth.jwt_handler import decode_jwt
from core.exceptions import AuthenticationError, AuthorizationError

PUBLIC_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
}


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        api_key     = request.headers.get("X-API-Key", "")

        user = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_jwt(token)
            except AuthenticationError as exc:
                return _unauth(str(exc))

            # Check blocklist
            redis = request.app.state.redis
            if redis and await redis.get(f"blocklist:{payload['jti']}"):
                return _unauth("Token has been revoked")

            if payload.get("type") != "access":
                return _unauth("Access token required")

            user = {
                "id":        payload["sub"],
                "roles":     payload["roles"],
                "auth_type": "jwt",
                "jti":       payload["jti"],
                "exp":       payload["exp"],
            }

        elif api_key:
            from core.auth.apikey_store import APIKeyStore
            store = APIKeyStore(request.app.state.redis)
            meta  = await store.lookup(api_key)
            if not meta:
                return _unauth("Invalid API key")
            user = {
                "id":        meta["client_id"],
                "roles":     meta["roles"],
                "auth_type": "api_key",
                "rate_limit": meta["rate_limit"],
            }
        else:
            return _unauth("Authentication required")

        request.state.user = user
        return await call_next(request)


def _unauth(message: str) -> Response:
    body = json.dumps({"success": False, "data": None, "error": message, "trace_id": None})
    return Response(content=body, status_code=401, media_type="application/json")
