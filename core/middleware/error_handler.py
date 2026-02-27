"""Global error handler middleware — 4th in stack (innermost, wraps handlers).

Catches all unhandled exceptions and maps them to TrishulResponse(success=False).
No stack traces ever appear in API responses.
All 5xx are logged with trace_id.
"""

import logging
import traceback

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)

HTTP_STATUS_MAP = {
    "AuthenticationError": 401,
    "AuthorizationError":  403,
    "RateLimitExceeded":   429,
    "PluginNotFoundError": 404,
    "BusPublishError":     503,
    "StorageError":        503,
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = getattr(getattr(request, "state", None), "trace_id", None)
        try:
            return await call_next(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"success": False, "data": None, "error": exc.detail, "trace_id": trace_id},
            )
        except Exception as exc:
            exc_type = type(exc).__name__
            status   = HTTP_STATUS_MAP.get(exc_type, 500)
            if status >= 500:
                log.error(
                    "unhandled_exception",
                    extra={
                        "trace_id":   trace_id,
                        "exc_type":   exc_type,
                        "path":       request.url.path,
                        "traceback":  traceback.format_exc(),
                    },
                )
            return JSONResponse(
                status_code=status,
                content={
                    "success": False,
                    "data":    None,
                    "error":   str(exc) if status < 500 else "Internal server error",
                    "trace_id": trace_id,
                },
            )
