"""Query router — proxy endpoints for VictoriaLogs, InfluxDB, and NATS monitoring.

Endpoints
---------
GET /api/v1/events          → VictoriaLogs LogsQL query (FM + LOG events)
GET /api/v1/metrics         → InfluxDB PM metrics query
GET /api/v1/platform/streams → NATS JetStream stats via HTTP monitoring API
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Request, Query

from core.models.responses import TrishulResponse

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.get("/events")
async def query_events(
    request:  Request,
    domain:   str       = Query("ALL",  description="FM | LOG | ALL"),
    start:    str       = Query("-1h",  description="VictoriaLogs time range, e.g. -1h, -6h, -24h"),
    limit:    int       = Query(200,    le=1000),
    severity: str | None = Query(None, description="CRITICAL|MAJOR|MINOR|WARNING|CLEARED"),
    protocol: str | None = Query(None),
    q:        str       = Query("*",    description="Free-text LogsQL filter"),
) -> TrishulResponse:
    """Search VictoriaLogs for FM/LOG events with optional filters."""
    event_store = request.app.state.event_store

    filters: list[str] = []
    if domain and domain.upper() != "ALL":
        filters.append(f"domain:{domain.upper()}")
    if severity:
        filters.append(f"severity:{severity.upper()}")
    if protocol:
        filters.append(f"protocol:{protocol.lower()}")
    if q and q.strip() not in ("*", ""):
        filters.append(f"({q.strip()})")

    query_str = " AND ".join(filters) if filters else "*"

    try:
        records = await event_store.search(query_str, domain=None, start=start, limit=limit)
    except Exception as exc:
        return TrishulResponse(success=False, data={"error": str(exc), "events": []})

    return TrishulResponse(success=True, data={"events": records, "count": len(records)})


@router.get("/metrics")
async def query_metrics(
    request:   Request,
    start:     str       = Query("-1h"),
    source_ne: str | None = Query(None),
    limit:     int       = Query(500, le=5000),
) -> TrishulResponse:
    """Query InfluxDB for recent PM metric data points."""
    metrics_store = request.app.state.metrics_store
    try:
        records = await metrics_store.query_pm(
            source_ne=source_ne or None,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        return TrishulResponse(success=False, data={"error": str(exc), "records": []})

    return TrishulResponse(success=True, data={"records": records, "count": len(records)})


@router.get("/platform/streams")
async def platform_streams() -> TrishulResponse:
    """Proxy the NATS HTTP monitoring API to return JetStream stream statistics."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://nats:8222/jsz?accounts=true")
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        return TrishulResponse(success=False, data={"error": str(exc), "streams": []})

    streams = []
    for acct in (raw.get("account_details") or []):
        for s in (acct.get("stream_detail") or []):
            state = s.get("state", {})
            cfg   = s.get("config", {})
            streams.append({
                "name":      s.get("name", "?"),
                "subjects":  cfg.get("subjects", []),
                "messages":  state.get("messages",  0),
                "bytes":     state.get("bytes",     0),
                "consumers": len(s.get("consumer_detail") or []),
            })

    return TrishulResponse(success=True, data={
        "streams":         streams,
        "total_streams":   raw.get("streams",   0),
        "total_messages":  raw.get("messages",  0),
        "total_bytes":     raw.get("bytes",     0),
        "total_consumers": raw.get("consumers", 0),
        "server_id":       raw.get("server_id", ""),
    })
