"""Health check router — GET /health

3-state model: healthy | degraded | unhealthy
  healthy    — all dependencies ok
  degraded   — storage failure (InfluxDB or VictoriaLogs down); app still runs
  unhealthy  — NATS or Redis down (critical path broken)

Each dependency check has a 2-second timeout.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.config.settings import get_settings

log = logging.getLogger(__name__)
router = APIRouter(tags=["platform"])

DepStatus = Literal["ok", "error"]
AppStatus = Literal["healthy", "degraded", "unhealthy"]

TIMEOUT = 2.0   # seconds per dependency check


async def _check_nats(app) -> DepStatus:
    try:
        client = app.state.nats_client
        return "ok" if client and client.is_connected else "error"
    except Exception:
        return "error"


async def _check_redis(app) -> DepStatus:
    try:
        await asyncio.wait_for(app.state.redis.ping(), timeout=TIMEOUT)
        return "ok"
    except Exception:
        return "error"


async def _check_influxdb(app) -> DepStatus:
    try:
        ok = await asyncio.wait_for(app.state.metrics_store.health(), timeout=TIMEOUT)
        return "ok" if ok else "error"
    except Exception:
        return "error"


async def _check_vlogs(app) -> DepStatus:
    try:
        ok = await asyncio.wait_for(app.state.event_store.health(), timeout=TIMEOUT)
        return "ok" if ok else "error"
    except Exception:
        return "error"


@router.get("/health")
async def health(request: Request):
    app = request.app

    nats_s, redis_s, influx_s, vlogs_s = await asyncio.gather(
        _check_nats(app),
        _check_redis(app),
        _check_influxdb(app),
        _check_vlogs(app),
    )

    # Determine overall status
    if nats_s == "error" or redis_s == "error":
        status: AppStatus = "unhealthy"
    elif influx_s == "error" or vlogs_s == "error":
        status = "degraded"
    else:
        status = "healthy"

    # Plugin statuses
    registry = getattr(app.state, "plugin_registry", None)
    plugins  = {}
    if registry:
        for name, plugin in registry.plugins.items():
            plugins[name] = {"status": "ok", "version": getattr(plugin, "version", "unknown")}

    body = {
        "status":    status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version":   get_settings().app_version,
        "dependencies": {
            "nats":         {"status": nats_s},
            "redis":        {"status": redis_s},
            "influxdb":     {"status": influx_s},
            "victorialogs": {"status": vlogs_s},
        },
        "plugins": plugins,
    }

    http_status = 200 if status in ("healthy", "degraded") else 503
    return JSONResponse(status_code=http_status, content=body)
