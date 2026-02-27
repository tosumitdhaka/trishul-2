"""Auth middleware — validates JWT or API Key on every non-public request.

Execution position: 3rd in middleware stack
  RateLimitMiddleware → RequestLoggingMiddleware → AuthMiddleware → ErrorHandlerMiddleware

Public paths bypass auth entirely.
All other requests must carry:
  Authorization: Bearer <JWT>   OR
  X-API-Key: <raw_key>

On success: attaches request.state.user = { id, username/client_id, roles, auth_type }
On failure: returns 401 TrishulResponse immediately.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.auth.apikey_store import lookup_key_in_redis
from core.auth.jwt_handler import AuthenticationError, decode_jwt

PUBLIC_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # --- JWT Bearer ---
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_jwt(token)
            except AuthenticationError as exc:
                return _unauthorized(str(exc))

            # Check Redis blocklist (jti)
            redis = request.app.state.redis
            jti = payload.get("jti", "")
            if await redis.exists(f"blocklist:{jti}"):
                return _unauthorized("Token has been revoked")

            request.state.user = {
                "id":        payload["sub"],
                "roles":     payload.get("roles", []),
                "auth_type": "jwt",
                "token_type": payload.get("type", "access"),
            }
            return await call_next(request)

        # --- API Key ---
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            redis = request.app.state.redis
            key_meta = await lookup_key_in_redis(redis, api_key)
            if not key_meta:
                return _unauthorized("Invalid or revoked API key")

            request.state.user = {
                "id":        key_meta["client_id"],
                "roles":     key_meta["roles"],
                "auth_type": "apikey",
            }
            return await call_next(request)

        return _unauthorized("Authentication required")


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"success": False, "data": None, "error": message, "trace_id": None},
    )


def require_role(*required_roles: str):
    """FastAPI route dependency that enforces RBAC.

    Usage:
        @router.post("/admin-action")
        async def admin_action(user=Depends(require_role("admin"))):
            ...
    """
    from fastapi import Depends, HTTPException
    from core.dependencies import get_current_user

    def checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(user.get("roles", []))
        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: requires one of {list(required_roles)}",
            )
        return user

    return Depends(checker)
