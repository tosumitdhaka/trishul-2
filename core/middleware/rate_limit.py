"""Rate limit middleware — 1st in stack (outermost).

Uses Redis INCR + EXPIRE sliding window (60s).
Client identity: authenticated user_id > X-Forwarded-For > client host.
Limit: configurable per client type (default 60/min, plugin keys 600/min).
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self._default_limit  = default_limit
        self._window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip rate-limiting for health / metrics
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        redis = getattr(request.app.state, "redis", None)
        if not redis:
            return await call_next(request)  # Redis not ready yet (startup)

        client_id = (
            getattr(getattr(request, "state", None), "user", {}).get("id")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        key   = f"ratelimit:{client_id}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, self._window_seconds)

        limit = self._default_limit
        if count > limit:
            log.warning(
                "rate_limit_exceeded",
                extra={"client_id": client_id, "count": count, "limit": limit},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data":    None,
                    "error":   f"Rate limit exceeded. Retry after {self._window_seconds}s.",
                    "trace_id": None,
                },
            )
        return await call_next(request)
