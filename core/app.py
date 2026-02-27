"""Trishul — FastAPI application factory with full lifespan management."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config.settings import get_settings
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
from core.ws.router import router as ws_router
from core.plugins_registry_router import router as plugins_registry_router

# Transformer
from transformer.router import router as transform_router
from transformer.pipeline import pipeline_registry
from transformer.decoders.json import JSONDecoder
from transformer.decoders.csv import CSVDecoder
from transformer.decoders.xml import XMLDecoder
from transformer.decoders.ves import VESDecoder
from transformer.decoders.snmp import SNMPDecoder
from transformer.decoders.protobuf import ProtobufDecoder
from transformer.decoders.avro import AvroDecoder
from transformer.encoders.json import JSONEncoder
from transformer.encoders.csv import CSVEncoder
from transformer.encoders.protobuf import ProtobufEncoder
from transformer.encoders.avro import AvroEncoder
from transformer.readers.file import FileReader
from transformer.readers.webhook import WebhookReader
from transformer.readers.http_poll import HTTPPollReader

import structlog

log = structlog.get_logger(__name__)


def _register_pipeline_stages() -> None:
    pipeline_registry.register_decoder("json",     JSONDecoder())
    pipeline_registry.register_decoder("csv",      CSVDecoder())
    pipeline_registry.register_decoder("xml",      XMLDecoder())
    pipeline_registry.register_decoder("ves",      VESDecoder())
    pipeline_registry.register_decoder("snmp",     SNMPDecoder())
    pipeline_registry.register_decoder("protobuf", ProtobufDecoder())
    pipeline_registry.register_decoder("avro",     AvroDecoder())
    pipeline_registry.register_encoder("json",     JSONEncoder())
    pipeline_registry.register_encoder("csv",      CSVEncoder())
    pipeline_registry.register_encoder("protobuf", ProtobufEncoder())
    pipeline_registry.register_encoder("avro",     AvroEncoder())
    pipeline_registry.register_reader("file",      FileReader())
    pipeline_registry.register_reader("webhook",   WebhookReader())
    pipeline_registry.register_reader("http_poll", HTTPPollReader())
    log.info("pipeline_stages_registered", stages=pipeline_registry.list_stages())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info("startup_begin", env=settings.APP_ENV)

    _register_pipeline_stages()

    nats = get_nats_client()
    await nats.connect(settings.NATS_URL)
    await provision_streams(nats)
    log.info("nats_connected", url=settings.NATS_URL)

    from transformer.readers.nats import NATSReader
    from transformer.writers.nats import NATSWriter
    pipeline_registry.register_reader("nats", NATSReader(nats))
    pipeline_registry.register_writer("nats", NATSWriter(nats))
    app.state.pipeline_registry = pipeline_registry

    metrics_store, event_store = get_stores(settings.STORAGE_MODE)
    app.state.metrics_store = metrics_store
    app.state.event_store   = event_store
    log.info("storage_ready", mode=settings.STORAGE_MODE)

    from transformer.writers.influxdb import InfluxDBWriter
    from transformer.writers.victorialogs import VictoriaLogsWriter
    pipeline_registry.register_writer("influxdb",     InfluxDBWriter(metrics_store))
    pipeline_registry.register_writer("victorialogs", VictoriaLogsWriter(event_store))

    registry = PluginRegistry()
    await registry.load_all(app, nats, metrics_store, event_store)
    app.state.plugin_registry = registry
    log.info("plugins_loaded", count=len(registry.plugins))

    notification_service = NotificationService(nats, metrics_store, event_store)
    await notification_service.start()
    app.state.notification_service = notification_service

    log.info(
        "startup_complete",
        plugins=list(registry.plugins.keys()),
        pipeline_stages=pipeline_registry.list_stages(),
    )
    yield

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

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router,              prefix="/api/v1")
    app.include_router(health_router)
    app.include_router(transform_router,         prefix="/api/v1")
    app.include_router(ws_router)                # /ws/events
    app.include_router(plugins_registry_router)  # /api/v1/plugins/registry

    return app


app = create_app()
