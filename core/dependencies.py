"""FastAPI Depends() wrappers — all shared resources injected from here.

Route handlers must NEVER import Redis/NATS/storage clients directly.
Always use these dependency functions.
"""

from typing import Annotated

from fastapi import Depends, Request

from core.config.settings import Settings, get_settings

# ─── Settings ──────────────────────────────────────────────────────────────

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ─── Auth (set by AuthMiddleware) ──────────────────────────────────────────

def get_current_user(request: Request) -> dict:
    """Returns the authenticated user dict attached by AuthMiddleware.

    Keys: id, username, roles, auth_type (jwt | apikey)
    """
    return request.state.user


CurrentUser = Annotated[dict, Depends(get_current_user)]


# ─── NATS client ───────────────────────────────────────────────────────────

def get_nats_client(request: Request):
    """Returns the NATS client attached to app state at startup."""
    return request.app.state.nats_client


NatsClient = Annotated[object, Depends(get_nats_client)]


# ─── Storage ───────────────────────────────────────────────────────────────

def get_metrics_store(request: Request):
    """Returns the MetricsStore instance (InfluxDB)."""
    return request.app.state.metrics_store


def get_event_store(request: Request):
    """Returns the EventStore instance (VictoriaLogs)."""
    return request.app.state.event_store


MetricsStoreDep = Annotated[object, Depends(get_metrics_store)]
EventStoreDep   = Annotated[object, Depends(get_event_store)]


# ─── Redis ─────────────────────────────────────────────────────────────────

def get_redis(request: Request):
    """Returns the async Redis client attached to app state at startup."""
    return request.app.state.redis


RedisDep = Annotated[object, Depends(get_redis)]
