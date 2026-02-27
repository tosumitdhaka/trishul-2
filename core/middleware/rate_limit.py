from __future__ import annotations

import json
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple fixed-window rate limiter using Redis INCR + EXPIRE.
    Key: ratelimit:{client_id}  — resets every 60s.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from core.config.settings import get_settings
        settings = get_settings()

        redis = request.app.state.redis
        # Identify client: authenticated user id or IP
        client_id = getattr(
            getattr(request.state, "user", None), "get", lambda k, d=None: None
        )("id") or (request.client.host if request.client else "anon")

        # Determine limit (plugin API keys may have higher limit)
        user = getattr(request.state, "user", {})
        auth_type = user.get("auth_type") if isinstance(user, dict) else None
        limit = settings.rate_limit_plugin if auth_type == "api_key" else settings.rate_limit_default

        key = f"ratelimit:{client_id}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)

        if count > limit:
            log.warning(
                json.dumps({"event": "rate_limit_exceeded", "client_id": client_id, "count": count})
            )
            body = json.dumps({"success": False, "error": f"Rate limit exceeded. Retry after 60s.", "data": None})
            return Response(content=body, status_code=429, media_type="application/json")

        return await call_next(request)
