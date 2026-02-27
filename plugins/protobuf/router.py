"""Protobuf plugin HTTP endpoints."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException

from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.protobuf.config import get_protobuf_settings
from plugins.protobuf.models import ProtobufReceiveRequest, ProtobufSimulateRequest
from plugins.protobuf.simulator import protobuf_simulator
from plugins.protobuf.pipeline import build_protobuf_pipeline

router = APIRouter(tags=["protobuf"])


@router.post("/protobuf/receive", status_code=202)
async def protobuf_receive(body: ProtobufReceiveRequest, request: Request):
    cfg      = get_protobuf_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    meta = {
        "domain":      body.domain,
        "protocol":    "protobuf",
        "source_ne":   body.source_ne,
        "direction":   "inbound",
        "trace_id":    trace_id,
        "raw_payload": body.payload,
        "timestamp":   datetime.now(timezone.utc),
    }

    pipeline = build_protobuf_pipeline(nats, cfg.PROTO_NATS_SUBJECT)
    envelope = await pipeline.run(body.payload, meta, {"subject": cfg.PROTO_NATS_SUBJECT})
    return AcceptedResponse(envelope_id=envelope.id, trace_id=trace_id)


@router.post("/protobuf/simulate")
async def protobuf_simulate(body: ProtobufSimulateRequest, request: Request):
    cfg      = get_protobuf_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    pipeline = build_protobuf_pipeline(nats, cfg.PROTO_SIM_SUBJECT)

    envelope_ids = []
    for item in protobuf_simulator.generate_batch(
        count=body.count, source_ne=body.source_ne, domain=body.domain
    ):
        meta = {
            "domain":      body.domain,
            "protocol":    "protobuf",
            "source_ne":   body.source_ne,
            "direction":   "simulated",
            "trace_id":    trace_id,
            "raw_payload": item,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await pipeline.run(item, meta, {"subject": cfg.PROTO_SIM_SUBJECT})
        envelope_ids.append(envelope.id)

    return TrishulResponse(success=True,
                           data={"envelope_ids": envelope_ids, "count": len(envelope_ids)},
                           trace_id=trace_id)


@router.get("/protobuf/health")
async def protobuf_health():
    return TrishulResponse(success=True, data={"plugin": "protobuf", "status": "healthy"})
