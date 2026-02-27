"""Webhook plugin router — /api/v1/webhook/*

Endpoints:
  POST /receive   — accept JSON payload → validate → publish to NATS → 202
  POST /send      — POST to external target URL
  POST /simulate  — generate N synthetic events, publish each to NATS
  GET  /status/{envelope_id}  — check envelope processing status from Redis
  GET  /health    — plugin-level health (always 200 if process is up)
"""

import json
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.bus.publisher import publish_envelope, publish_sim
from core.dependencies import CurrentUser
from core.models.envelope import Direction, FCAPSDomain, MessageEnvelope, Severity
from core.models.responses import AcceptedResponse, TrishulResponse
from plugins.webhook.models import SimulateRequest, WebhookPayload
from plugins.webhook.simulator import generate_events
from transformer.normalizer import FCAPSNormalizer

router = APIRouter(tags=["webhook"])
_normalizer = FCAPSNormalizer()


# ─── Receive ─────────────────────────────────────────────────────────────────────

@router.post("/receive", response_model=AcceptedResponse, status_code=202)
async def receive(
    payload: WebhookPayload,
    request: Request,
    user:    CurrentUser,
):
    trace_id = getattr(request.state, "trace_id", None)
    redis    = request.app.state.redis

    # Dedup check
    env_id = str(uuid.uuid4())
    dedup_key = f"dedup:{env_id}"
    if await redis.exists(dedup_key):
        return AcceptedResponse(envelope_id=env_id, message="Duplicate — already queued")

    # Normalize to MessageEnvelope
    envelope = await _normalizer.normalize(
        decoded=payload.model_dump(),
        meta={
            "domain":      FCAPSDomain(payload.domain),
            "protocol":    "webhook",
            "source_ne":   payload.source_ne,
            "direction":   Direction.INBOUND,
            "raw_payload": payload.model_dump(),
            "trace_id":    trace_id,
            "severity":    payload.severity,
        },
    )
    envelope.id = env_id

    # Publish to NATS
    await publish_envelope(envelope)

    # Cache dedup entry (15 min)
    await redis.setex(dedup_key, 900, json.dumps({"status": "queued", "domain": envelope.domain}))

    return AcceptedResponse(envelope_id=env_id)


# ─── Send ───────────────────────────────────────────────────────────────────────────

class _SendIn(BaseModel):
    target_url: str
    payload:    dict


@router.post("/send", response_model=TrishulResponse)
async def send(body: _SendIn, user: CurrentUser):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(body.target_url, json=body.payload)
            return TrishulResponse.ok(data={"status_code": resp.status_code, "sent": True})
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Send failed: {exc}") from exc


# ─── Simulate ───────────────────────────────────────────────────────────────────────

@router.post("/simulate", response_model=TrishulResponse)
async def simulate(req: SimulateRequest, request: Request, user: CurrentUser):
    trace_id     = getattr(request.state, "trace_id", None)
    events       = generate_events(req)
    envelope_ids = []

    for event in events:
        envelope = await _normalizer.normalize(
            decoded=event,
            meta={
                "domain":    FCAPSDomain(req.domain),
                "protocol":  "webhook",
                "source_ne": req.source_ne,
                "direction": Direction.SIMULATED,
                "trace_id":  trace_id,
                "severity":  event.get("severity"),
            },
        )
        await publish_sim(envelope)
        envelope_ids.append(envelope.id)

    return TrishulResponse.ok(data={"sent": len(events), "envelope_ids": envelope_ids})


# ─── Status ───────────────────────────────────────────────────────────────────────

@router.get("/status/{envelope_id}", response_model=TrishulResponse)
async def status(envelope_id: str, request: Request, user: CurrentUser):
    redis = request.app.state.redis
    raw   = await redis.get(f"dedup:{envelope_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Envelope not found or expired")
    data = json.loads(raw)
    return TrishulResponse.ok(data={"envelope_id": envelope_id, **data})


# ─── Plugin Health ──────────────────────────────────────────────────────────────────

@router.get("/health", response_model=TrishulResponse)
async def plugin_health():
    return TrishulResponse.ok(data={"plugin": "webhook", "status": "ok", "version": "1.0.0"})
