"""SFTP plugin HTTP endpoints."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException

from core.models.responses import TrishulResponse, AcceptedResponse
from plugins.sftp.config import get_sftp_settings
from plugins.sftp.models import SFTPReceiveRequest, SFTPSimulateRequest
from plugins.sftp.simulator import sftp_simulator
from plugins.sftp.pipeline import build_sftp_pipeline

router = APIRouter(tags=["sftp"])


@router.post("/sftp/receive", status_code=202)
async def sftp_receive(body: SFTPReceiveRequest, request: Request):
    cfg      = get_sftp_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    meta = {
        "domain":      body.domain,
        "protocol":    "sftp",
        "source_ne":   body.source_ne,
        "direction":   "inbound",
        "trace_id":    trace_id,
        "raw_payload": body.payload,
        "timestamp":   datetime.now(timezone.utc),
    }

    pipeline = build_sftp_pipeline(nats, cfg.SFTP_NATS_SUBJECT)
    envelope = await pipeline.run(body.payload, meta, {"subject": cfg.SFTP_NATS_SUBJECT})
    return AcceptedResponse(envelope_id=envelope.id, trace_id=trace_id)


@router.post("/sftp/simulate")
async def sftp_simulate(body: SFTPSimulateRequest, request: Request):
    cfg      = get_sftp_settings()
    nats     = request.app.state.nats
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    pipeline = build_sftp_pipeline(nats, cfg.SFTP_SIM_SUBJECT)

    envelope_ids = []
    for item in sftp_simulator.generate_batch(
        count=body.count, source_ne=body.source_ne, domain=body.domain
    ):
        meta = {
            "domain":      body.domain,
            "protocol":    "sftp",
            "source_ne":   body.source_ne,
            "direction":   "simulated",
            "trace_id":    trace_id,
            "raw_payload": item,
            "timestamp":   datetime.now(timezone.utc),
        }
        envelope = await pipeline.run(item, meta, {"subject": cfg.SFTP_SIM_SUBJECT})
        envelope_ids.append(envelope.id)

    return TrishulResponse(success=True,
                           data={"envelope_ids": envelope_ids, "count": len(envelope_ids)},
                           trace_id=trace_id)


@router.get("/sftp/health")
async def sftp_health():
    return TrishulResponse(success=True, data={"plugin": "sftp", "status": "healthy"})
