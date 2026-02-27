"""Trishul — FastAPI application factory with full lifespan management."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config.settings import get_settings
from core.exceptions import TrishulException
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.logging import RequestLoggingMiddleware
from core.middleware.error_handler import ErrorHandlerMiddleware
from core.bus.client import get_nats_client
from core.bus.streams import provision_streams
from core.storage.factory import get_stores
from core.plugin_registry import PluginRegistry
from core.auth.router import router as auth_router
from core.health.router import router as health_router
from core.notifications.service import NotificationService
import logging
import structlog

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info("startup_begin", env=settings.APP_ENV)

    # 1. NATS connection + stream provisioning
    nats = get_nats_client()
    await nats.connect(settings.NATS_URL)
    await provision_streams(nats)
    log.info("nats_connected", url=settings.NATS_URL)

    # 2. Storage adapters
    metrics_store, event_store = get_stores(settings.STORAGE_MODE)
    app.state.metrics_store = metrics_store
    app.state.event_store = event_store
    log.info("storage_ready", mode=settings.STORAGE_MODE)

    # 3. Plugin auto-discovery and registration
    registry = PluginRegistry()
    await registry.load_all(app, nats, metrics_store, event_store)
    app.state.plugin_registry = registry
    log.info("plugins_loaded", count=len(registry.plugins))

    # 4. Start NATS consumers (storage-writer + ws-broadcaster)
    notification_service = NotificationService(nats, metrics_store, event_store)
    await notification_service.start()
    app.state.notification_service = notification_service

    log.info("startup_complete", plugins=list(registry.plugins.keys()))
    yield

    # Shutdown
    log.info("shutdown_begin")
    await registry.shutdown_all()
    await notification_service.stop()
    await nats.drain()
    log.info("shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Trishul FCAPS Platform",
        description="FCAPS Simulation, Parsing & Visualization Platform",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware — order matters: added last = executes first
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in prod
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routers
    app.include_router(auth_router,   prefix="/api/v1")
    app.include_router(health_router)

    return app


app = create_app()
