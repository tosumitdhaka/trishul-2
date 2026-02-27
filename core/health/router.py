from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from core.config.settings import get_settings

log = logging.getLogger(__name__)
router = APIRouter(tags=["platform"])

_TIMEOUT = 2.0  # seconds per dependency check


async def _check_nats(nc) -> dict:
    try:
        # JetStream account info is the lightest check
        await asyncio.wait_for(nc.jetstream().find_stream("FCAPS_INGEST"), timeout=_TIMEOUT)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


async def _check_redis(r: aioredis.Redis) -> dict:
    try:
        await asyncio.wait_for(r.ping(), timeout=_TIMEOUT)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


async def _check_storage(store) -> dict:
    try:
        ok = await asyncio.wait_for(store.health(), timeout=_TIMEOUT)
        return {"status": "ok"} if ok else {"status": "error", "detail": "health() returned False"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/health")
async def health(request: Request):
    app = request.app
    nats_r, redis_r, influx_r, vlogs_r = await asyncio.gather(
        _check_nats(app.state.nats),
        _check_redis(app.state.redis),
        _check_storage(app.state.metrics_store),
        _check_storage(app.state.event_store),
    )

    critical_down = nats_r["status"] == "error" or redis_r["status"] == "error"
    storage_down  = influx_r["status"] == "error" or vlogs_r["status"] == "error"

    if critical_down:
        overall = "unhealthy"
    elif storage_down:
        overall = "degraded"
    else:
        overall = "healthy"

    plugins = {
        name: {"status": "ok", "version": p.version}
        for name, p in app.state.plugin_registry.plugins.items()
    }

    payload = {
        "status":    overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version":   get_settings().app_version,
        "dependencies": {
            "nats":         nats_r,
            "redis":        redis_r,
            "influxdb":     influx_r,
            "victorialogs": vlogs_r,
        },
        "plugins": plugins,
    }
    status_code = 200 if overall != "unhealthy" else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics(request: Request):
    """Prometheus text format stub — real counters wired in core/app.py."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
