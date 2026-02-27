"""Avro plugin HTTP endpoints."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException

from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.avro.config import get_avro_settings
from plugins.avro.models import AvroReceiveRequest, AvroSimulateRequest
from plugins.avro.simulator import avro_simulator
from plugins.avro.pipeline import build_avro_pipeline

router = APIRouter(tags=["avro"])


@router.post("/avro/receive", status_code=202)
async def avro_receive(body: AvroReceiveRequest, request: Request):
    cfg      = get_avro_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    meta = {
        "domain":      body.domain,
        "protocol":    "avro",
        "source_ne":   body.source_ne,
        "direction":   "inbound",
        "trace_id":    trace_id,
        "raw_payload": body.payload,
        "timestamp":   datetime.now(timezone.utc),
    }

    pipeline = build_avro_pipeline(nats, cfg.AVRO_NATS_SUBJECT)
    envelope = await pipeline.run(body.payload, meta, {"subject": cfg.AVRO_NATS_SUBJECT})
    return AcceptedResponse(envelope_id=envelope.id, trace_id=trace_id)


@router.post("/avro/simulate")
async def avro_simulate(body: AvroSimulateRequest, request: Request):
    cfg      = get_avro_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    pipeline = build_avro_pipeline(nats, cfg.AVRO_SIM_SUBJECT)

    envelope_ids = []
    for item in avro_simulator.generate_batch(
        count=body.count, source_ne=body.source_ne, domain=body.domain
    ):
        meta = {
            "domain":      body.domain,
            "protocol":    "avro",
            "source_ne":   body.source_ne,
            "direction":   "simulated",
            "trace_id":    trace_id,
            "raw_payload": item,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await pipeline.run(item, meta, {"subject": cfg.AVRO_SIM_SUBJECT})
        envelope_ids.append(envelope.id)

    return TrishulResponse(success=True,
                           data={"envelope_ids": envelope_ids, "count": len(envelope_ids)},
                           trace_id=trace_id)


@router.get("/avro/health")
async def avro_health():
    return TrishulResponse(success=True, data={"plugin": "avro", "status": "healthy"})
