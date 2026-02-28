"""Webhook plugin HTTP router — 5 standard endpoints."""
import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.bus.publisher import publish_envelope
from core.models.envelope import MessageEnvelope, FCAPSDomain, Direction, Severity
from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.webhook.models import WebhookPayload, SimulateRequest, SendRequest
from plugins.webhook.simulator import generate_events
from transformer.normalizer import fcaps_normalizer

import uuid
from datetime import datetime, timezone

log = structlog.get_logger(__name__)

# prefix=/api/v1 is added by PluginRegistry; plugin name segment must be here.
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/receive", response_model=AcceptedResponse, status_code=202)
async def receive(payload: WebhookPayload, request: Request):
    """Accept inbound webhook event, publish to NATS, return 202."""
    trace_id    = getattr(request.state, "trace_id", None)
    envelope_id = str(uuid.uuid4())

    redis = request.app.state.redis
    if redis:
        dedup_key = f"dedup:{envelope_id}"
        if await redis.exists(dedup_key):
            return AcceptedResponse(envelope_id=envelope_id, status="duplicate")
        await redis.setex(dedup_key, 900, "processing")

    decoded = payload.model_dump()
    meta = {
        "envelope_id": envelope_id,
        "domain":      payload.domain,
        "protocol":    "webhook",
        "source_ne":   payload.source_ne,
        "direction":   "inbound",
        "severity":    payload.severity,
        "trace_id":    trace_id,
        "raw_payload": decoded,
        "timestamp":   datetime.now(timezone.utc),
    }
    envelope = await fcaps_normalizer.normalize(decoded, meta)

    nats = request.app.state.nats
    await publish_envelope(nats, envelope, "fcaps.ingest.webhook")

    log.info("envelope_ingested", envelope_id=envelope_id, domain=payload.domain, trace_id=trace_id)
    return AcceptedResponse(envelope_id=envelope_id)


@router.post("/send")
async def send(body: SendRequest, request: Request):
    """POST a webhook payload to a target URL."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(body.target_url, json=body.payload)
    return TrishulResponse(success=True, data={"status_code": resp.status_code})


@router.post("/simulate")
async def simulate(body: SimulateRequest, request: Request):
    """Generate synthetic events and publish to fcaps.simulated.webhook."""
    events       = generate_events(body.count, body.domain, body.severity, body.source_ne)
    envelope_ids = []

    for event in events:
        envelope_id = str(uuid.uuid4())
        decoded = event.model_dump()
        meta = {
            "envelope_id": envelope_id,
            "domain":      event.domain,
            "protocol":    "webhook",
            "source_ne":   event.source_ne,
            "direction":   "simulated",
            "severity":    event.severity,
            "trace_id":    getattr(request.state, "trace_id", None),
            "raw_payload": decoded,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await fcaps_normalizer.normalize(decoded, meta)
        nats = request.app.state.nats
        await publish_envelope(nats, envelope, "fcaps.simulated.webhook")
        envelope_ids.append(envelope_id)

    return TrishulResponse(success=True, data={"sent": body.count, "envelope_ids": envelope_ids})


@router.get("/status/{envelope_id}")
async def status(envelope_id: str, request: Request):
    redis = request.app.state.redis
    if redis:
        val = await redis.get(f"dedup:{envelope_id}")
        if val:
            return TrishulResponse(success=True, data={"envelope_id": envelope_id, "status": val})
    return TrishulResponse(success=True, data={"envelope_id": envelope_id, "status": "not_found"})


@router.get("/health")
async def health():
    return TrishulResponse(success=True, data={"plugin": "webhook", "status": "ok"})
