"""SNMP plugin HTTP endpoints."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException

from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.snmp.config import get_snmp_settings
from plugins.snmp.models import SNMPTrapRequest, SNMPSimulateRequest
from plugins.snmp.simulator import snmp_simulator
from plugins.snmp.pipeline import build_snmp_pipeline
from transformer.decoders.snmp import SNMPDecoder

router = APIRouter(tags=["snmp"])
_decoder = SNMPDecoder()


@router.post("/snmp/receive", status_code=202)
async def snmp_receive(trap: SNMPTrapRequest, request: Request):
    """Accept a pre-parsed SNMP trap, run through pipeline, publish to NATS."""
    cfg      = get_snmp_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    raw = trap.model_dump()
    meta = {
        "domain":      "FM",
        "protocol":    "snmp",
        "source_ne":   trap.agent_address,
        "direction":   "inbound",
        "trace_id":    trace_id,
        "raw_payload": raw,
        "timestamp":   datetime.now(timezone.utc),
    }

    pipeline = build_snmp_pipeline(nats, cfg.SNMP_NATS_SUBJECT)
    envelope = await pipeline.run(raw, meta, {"subject": cfg.SNMP_NATS_SUBJECT})

    return AcceptedResponse(envelope_id=envelope.id, trace_id=trace_id)


@router.post("/snmp/simulate")
async def snmp_simulate(body: SNMPSimulateRequest, request: Request):
    cfg      = get_snmp_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    pipeline = build_snmp_pipeline(nats, cfg.SNMP_SIM_SUBJECT)

    envelope_ids = []
    for trap_dict in snmp_simulator.generate_batch(
        count=body.count, trap_type=body.trap_type,
        source_ne=body.source_ne, domain=body.domain,
    ):
        meta = {
            "domain":      body.domain,
            "protocol":    "snmp",
            "source_ne":   body.source_ne,
            "direction":   "simulated",
            "trace_id":    trace_id,
            "raw_payload": trap_dict,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await pipeline.run(trap_dict, meta, {"subject": cfg.SNMP_SIM_SUBJECT})
        envelope_ids.append(envelope.id)

    return TrishulResponse(success=True,
                           data={"envelope_ids": envelope_ids, "count": len(envelope_ids)},
                           trace_id=trace_id)


@router.get("/snmp/status/{envelope_id}")
async def snmp_status(envelope_id: str, request: Request):
    redis = request.app.state.redis
    if redis:
        raw = await redis.get(f"envelope:{envelope_id}")
        if raw:
            return TrishulResponse(success=True, data=json.loads(raw))
    raise HTTPException(status_code=404, detail=f"Envelope {envelope_id} not found")


@router.get("/snmp/health")
async def snmp_health():
    return TrishulResponse(success=True, data={"plugin": "snmp", "status": "healthy"})
