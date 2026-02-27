"""VES plugin HTTP endpoints."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
import json

from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.ves.config import get_ves_settings
from plugins.ves.models import VESEventRequest, VESSimulateRequest
from plugins.ves.simulator import ves_simulator
from plugins.ves.pipeline import build_ves_pipeline

router = APIRouter(tags=["ves"])


@router.post("/ves/receive", status_code=202)
async def ves_receive(event: VESEventRequest, request: Request):
    cfg      = get_ves_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    header    = event.event.get("commonEventHeader", {})
    domain    = header.get("domain", "fault")
    source_ne = header.get("sourceName", "unknown")

    fcaps_domain_map = {
        "fault": "FM", "measurement": "PM",
        "syslog": "LOG", "log": "LOG", "heartbeat": "LOG",
    }
    fcaps_domain = fcaps_domain_map.get(domain.lower(), "LOG")

    meta = {
        "domain":      fcaps_domain,
        "protocol":    "ves",
        "source_ne":   source_ne,
        "direction":   "inbound",
        "trace_id":    trace_id,
        "raw_payload": event.model_dump(),
        "timestamp":   datetime.now(timezone.utc),
    }

    pipeline = build_ves_pipeline(nats, cfg.VES_NATS_SUBJECT)
    envelope = await pipeline.run({"event": event.event}, meta, {"subject": cfg.VES_NATS_SUBJECT})

    return AcceptedResponse(envelope_id=envelope.id, trace_id=trace_id)


@router.post("/ves/simulate")
async def ves_simulate(body: VESSimulateRequest, request: Request):
    cfg      = get_ves_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    pipeline = build_ves_pipeline(nats, cfg.VES_SIM_SUBJECT)

    fcaps_domain_map = {
        "fault": "FM", "measurement": "PM",
        "syslog": "LOG",
    }
    fcaps_domain = fcaps_domain_map.get(body.domain.lower(), "LOG")

    envelope_ids = []
    for ves_dict in ves_simulator.generate_batch(
        count=body.count, domain=body.domain,
        severity=body.severity, source_ne=body.source_ne,
    ):
        meta = {
            "domain":      fcaps_domain,
            "protocol":    "ves",
            "source_ne":   body.source_ne,
            "direction":   "simulated",
            "trace_id":    trace_id,
            "raw_payload": ves_dict,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await pipeline.run(ves_dict, meta, {"subject": cfg.VES_SIM_SUBJECT})
        envelope_ids.append(envelope.id)

    return TrishulResponse(success=True,
                           data={"envelope_ids": envelope_ids, "count": len(envelope_ids)},
                           trace_id=trace_id)


@router.get("/ves/status/{envelope_id}")
async def ves_status(envelope_id: str, request: Request):
    redis = request.app.state.redis
    if redis:
        raw = await redis.get(f"envelope:{envelope_id}")
        if raw:
            return TrishulResponse(success=True, data=json.loads(raw))
    raise HTTPException(status_code=404, detail=f"Envelope {envelope_id} not found")


@router.get("/ves/health")
async def ves_health():
    return TrishulResponse(success=True, data={"plugin": "ves", "status": "healthy"})
