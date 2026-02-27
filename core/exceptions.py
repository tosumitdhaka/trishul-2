"""All custom exceptions for Trishul. Import from here — never define elsewhere."""


class TrishulBaseError(Exception):
    """Base for all Trishul application errors."""


class AuthenticationError(TrishulBaseError):
    """401 — token invalid/expired or credentials wrong."""


class AuthorizationError(TrishulBaseError):
    """403 — authenticated but insufficient role."""


class RateLimitExceeded(TrishulBaseError):
    """429 — too many requests."""


class PluginNotFoundError(TrishulBaseError):
    """404 — plugin not registered."""


class BusPublishError(TrishulBaseError):
    """503 — NATS publish failed."""


class StorageError(TrishulBaseError):
    """503 — InfluxDB or VictoriaLogs write/read failed."""


class ValidationError(TrishulBaseError):
    """422 — payload failed business-logic validation (distinct from Pydantic)."""


class PipelineError(TrishulBaseError):
    """500 — Transformer pipeline stage failed."""
