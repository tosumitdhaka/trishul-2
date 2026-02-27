from __future__ import annotations

import json
import logging
import traceback
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusPublishError,
    PluginNotFoundError,
    RateLimitExceeded,
    StorageError,
    TrishulBaseError,
)

log = logging.getLogger(__name__)

_STATUS_MAP = {
    AuthenticationError:  401,
    AuthorizationError:   403,
    RateLimitExceeded:    429,
    PluginNotFoundError:  404,
    BusPublishError:      503,
    StorageError:         503,
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = getattr(request.state, "trace_id", None)
        try:
            return await call_next(request)
        except TrishulBaseError as exc:
            status = _STATUS_MAP.get(type(exc), 400)
            log.warning(
                json.dumps({"event": "handled_error", "type": type(exc).__name__,
                            "msg": str(exc), "trace_id": trace_id})
            )
            return _error_response(str(exc), status, trace_id)
        except Exception:
            log.error(
                json.dumps({"event": "unhandled_error", "trace_id": trace_id,
                            "traceback": traceback.format_exc()})
            )
            return _error_response("Internal server error", 500, trace_id)


def _error_response(msg: str, status: int, trace_id: str | None) -> Response:
    body = json.dumps({"success": False, "error": msg, "data": None, "trace_id": trace_id})
    return Response(content=body, status_code=status, media_type="application/json")
