"""FastAPI Depends() wrappers — all shared resources injected via these."""
from fastapi import Depends, Request
from core.config.settings import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()


def metrics_store_dep(request: Request):
    return request.app.state.metrics_store


def event_store_dep(request: Request):
    return request.app.state.event_store


def nats_dep(request: Request):
    return request.app.state.nats


def redis_dep(request: Request):
    return request.app.state.redis


def current_user(request: Request) -> dict:
    """Returns user dict set by AuthMiddleware."""
    user = getattr(request.state, "user", None)
    if user is None:
        from core.exceptions import AuthenticationError
        raise AuthenticationError("Not authenticated")
    return user


def require_role(*roles: str):
    """Dependency factory: raises 403 if user doesn't have any of the required roles."""
    def checker(user: dict = Depends(current_user)) -> dict:
        user_roles = set(user.get("roles", []))
        if not user_roles.intersection(roles):
            from core.exceptions import AuthorizationError
            raise AuthorizationError(f"Requires one of: {list(roles)}")
        return user
    return checker
