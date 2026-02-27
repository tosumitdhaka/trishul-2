"""JSON structured request/response logging middleware. Injects trace_id."""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import structlog

log = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        start = time.perf_counter()
        log.info(
            "request_received",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request_completed",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Trace-Id"] = trace_id
        return response
