"""Request logging middleware — 2nd in stack.

Generates a UUID trace_id per request and attaches it to request.state.
Logs JSON: method, path, status, client_ip, duration_ms, trace_id.
"""

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        t0 = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - t0) * 1000, 2)

        log.info(
            "request_completed",
            extra={
                "trace_id":    trace_id,
                "method":      request.method,
                "path":        request.url.path,
                "status":      response.status_code,
                "client_ip":   request.client.host if request.client else "unknown",
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Trace-Id"] = trace_id
        return response
