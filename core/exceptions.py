"""All custom exceptions — map to HTTP status codes in ErrorHandlerMiddleware."""


class TrishulException(Exception):
    """Base for all Trishul exceptions."""


class AuthenticationError(TrishulException):
    """401 — Missing / invalid / expired credentials."""


class AuthorizationError(TrishulException):
    """403 — Authenticated but lacks required role."""


class RateLimitExceeded(TrishulException):
    """429 — Too many requests."""


class PluginNotFoundError(TrishulException):
    """404 — Plugin not registered."""


class BusPublishError(TrishulException):
    """503 — NATS publish failed."""


class StorageError(TrishulException):
    """503 — Storage write/read failed."""


class ValidationError(TrishulException):
    """422 — Business-level validation failure (distinct from Pydantic)."""
