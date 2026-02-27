"""Global exception handler — every error becomes TrishulResponse."""
import json
from typing import Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import structlog

from core.exceptions import (
    AuthenticationError, AuthorizationError, RateLimitExceeded,
    PluginNotFoundError, BusPublishError, StorageError, TrishulException,
)

log = structlog.get_logger(__name__)

EXCEPTION_MAP = {
    AuthenticationError:   401,
    AuthorizationError:    403,
    RateLimitExceeded:     429,
    PluginNotFoundError:   404,
    BusPublishError:       503,
    StorageError:          503,
    RequestValidationError: 422,
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = getattr(request.state, "trace_id", None)
        try:
            return await call_next(request)
        except Exception as exc:
            status  = 500
            message = "Internal error"
            for exc_type, code in EXCEPTION_MAP.items():
                if isinstance(exc, exc_type):
                    status  = code
                    message = str(exc)
                    break

            if status >= 500:
                log.error("unhandled_exception", trace_id=trace_id, error=str(exc), exc_info=True)
            else:
                log.warning("handled_exception", trace_id=trace_id, status=status, error=str(exc))

            body = json.dumps({
                "success":  False,
                "data":     None,
                "error":    message,
                "trace_id": trace_id,
            })
            return Response(content=body, status_code=status, media_type="application/json")
