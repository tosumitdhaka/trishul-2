"""Health check endpoint — 3-state: healthy / degraded / unhealthy."""
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from core.config.settings import get_settings

router = APIRouter(tags=["platform"])


@router.get("/health")
async def health(request: Request):
    redis         = getattr(request.app.state, "redis", None)
    nats_client   = getattr(request.app.state, "nats", None)
    metrics_store = getattr(request.app.state, "metrics_store", None)
    event_store   = getattr(request.app.state, "event_store", None)
    registry      = getattr(request.app.state, "plugin_registry", None)

    async def check(name: str, coro):
        try:
            ok = await asyncio.wait_for(coro, timeout=2.0)
            return name, {"status": "ok" if ok else "error"}
        except Exception as exc:
            return name, {"status": "error", "detail": str(exc)}

    checks = await asyncio.gather(
        check("nats",         _ping_nats(nats_client)),
        check("redis",        _ping_redis(redis)),
        check("influxdb",     metrics_store.health() if metrics_store else _false()),
        check("victorialogs", event_store.health()   if event_store   else _false()),
    )
    deps = dict(checks)

    critical = {"nats", "redis"}
    if any(deps[k]["status"] == "error" for k in critical):
        overall = "unhealthy"
    elif any(v["status"] == "error" for v in deps.values()):
        overall = "degraded"
    else:
        overall = "healthy"

    plugins = {}
    if registry:
        for name, plugin in registry.plugins.items():
            plugins[name] = {"status": "ok", "version": plugin.version}

    status_code = 200 if overall == "healthy" else (207 if overall == "degraded" else 503)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status":       overall,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "version":      "1.0.0",
            "dependencies": deps,
            "plugins":      plugins,
        },
    )


async def _ping_nats(client) -> bool:
    """client is TrishulNATSClient; check its internal _nc."""
    if client is None:
        return False
    nc = getattr(client, "_nc", None)
    if nc is None:
        return False
    return nc.is_connected


async def _ping_redis(redis) -> bool:
    if redis is None:
        return False
    return await redis.ping()


async def _false() -> bool:
    return False
