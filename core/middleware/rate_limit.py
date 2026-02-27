"""Redis token-bucket rate limiter middleware."""
import json
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return await call_next(request)

        client_id = self._get_client_id(request)
        limit     = self._settings.RATE_LIMIT_DEFAULT
        key       = f"ratelimit:{client_id}"

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)

        if count > limit:
            body = json.dumps({
                "success": False, "data": None,
                "error": f"Rate limit exceeded. Retry after {await redis.ttl(key)}s",
                "trace_id": None,
            })
            return Response(content=body, status_code=429, media_type="application/json")

        return await call_next(request)

    @staticmethod
    def _get_client_id(request: Request) -> str:
        user = getattr(request.state, "user", None)
        if user:
            return user.get("id", request.client.host)
        return request.client.host
