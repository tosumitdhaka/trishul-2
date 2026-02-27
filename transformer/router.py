"""Transform API router — /api/v1/transform/* and /api/v1/schemas/* endpoints."""
import uuid
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from core.models.responses import TrishulResponse, AcceptedResponse
from transformer.pipeline import PipelineJobConfig, pipeline_registry
from transformer.normalizer import fcaps_normalizer
from transformer.schema_registry import SchemaRecord, get_schema_registry

router = APIRouter(tags=["transform"])


# ──────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    payload:    Any
    config:     PipelineJobConfig


class SubmitRequest(BaseModel):
    config:     PipelineJobConfig


class SchemaCreateRequest(BaseModel):
    id:      str
    name:    str
    format:  str          # 'avro' | 'protobuf'
    version: str
    content: str          # JSON schema text or .proto content


# ──────────────────────────────────────────────────────────────────
# Transform endpoints
# ──────────────────────────────────────────────────────────────────

@router.post("/transform/run")
async def transform_run(body: RunRequest, request: Request):
    """Sync pipeline: decode + normalise + encode + write inline, return envelope."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    try:
        pipeline = pipeline_registry.get_pipeline(body.config, fcaps_normalizer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    meta = {
        "domain":      body.config.normalizer.domain,
        "protocol":    body.config.normalizer.protocol,
        "source_ne":   body.config.normalizer.source_ne,
        "direction":   body.config.normalizer.direction,
        "trace_id":    trace_id,
        "raw_payload": body.payload if isinstance(body.payload, dict) else {},
        "timestamp":   datetime.now(timezone.utc),
    }

    # Payload may be dict or string (base64 for binary) — pass as-is to decoder
    raw = body.payload
    if isinstance(raw, str):
        raw = raw.encode("utf-8")

    envelope = await pipeline.run(
        raw        = raw,
        meta       = meta,
        sink_config = body.config.writer.model_extra or {},
    )

    return TrishulResponse(
        success  = True,
        data     = json.loads(envelope.model_dump_json()),
        trace_id = trace_id,
    )


@router.post("/transform/submit", status_code=202)
async def transform_submit(body: SubmitRequest, request: Request):
    """Async pipeline job: publish PipelineJobConfig to NATS job queue, return job_id."""
    job_id   = str(uuid.uuid4())
    trace_id = getattr(request.state, "trace_id", job_id)

    nats = request.app.state.nats
    payload = json.dumps({
        "job_id":    job_id,
        "config":    body.config.model_dump(),
        "trace_id":  trace_id,
        "submitted": datetime.now(timezone.utc).isoformat(),
    }).encode()

    await nats.js.publish("fcaps.process.transform", payload)

    # Track in Redis so /jobs/{id} can return status
    redis = request.app.state.redis
    if redis:
        await redis.setex(
            f"job:{job_id}",
            3600,
            json.dumps({"status": "queued", "trace_id": trace_id}),
        )

    return TrishulResponse(
        success  = True,
        data     = {"job_id": job_id, "status": "queued"},
        trace_id = trace_id,
    )


@router.get("/transform/jobs/{job_id}")
async def transform_job_status(job_id: str, request: Request):
    """Get async job status from Redis."""
    redis = request.app.state.redis
    if not redis:
        raise HTTPException(status_code=503, detail="Redis unavailable")

    raw = await redis.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return TrishulResponse(
        success = True,
        data    = json.loads(raw),
    )


@router.get("/transform/stages")
async def list_stages():
    """List all registered readers, decoders, encoders, writers."""
    return TrishulResponse(
        success = True,
        data    = pipeline_registry.list_stages(),
    )


# ──────────────────────────────────────────────────────────────────
# Schema Registry endpoints
# ──────────────────────────────────────────────────────────────────

@router.post("/schemas", status_code=201)
async def create_schema(body: SchemaCreateRequest):
    reg    = get_schema_registry()
    record = reg.create(
        schema_id = body.id,
        name      = body.name,
        fmt       = body.format,
        version   = body.version,
        content   = body.content,
    )
    return TrishulResponse(success=True, data={
        "id": record.id, "name": record.name,
        "format": record.format, "version": record.version,
    })


@router.get("/schemas")
async def list_schemas():
    reg     = get_schema_registry()
    records = reg.list_all()
    return TrishulResponse(success=True, data=[
        {"id": r.id, "name": r.name, "format": r.format, "version": r.version}
        for r in records
    ])


@router.get("/schemas/{schema_id}")
async def get_schema(schema_id: str):
    reg    = get_schema_registry()
    record = reg.get(schema_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Schema '{schema_id}' not found")
    return TrishulResponse(success=True, data={
        "id": record.id, "name": record.name, "format": record.format,
        "version": record.version, "content": record.content,
        "created_at": record.created_at.isoformat(),
    })


@router.delete("/schemas/{schema_id}")
async def delete_schema(schema_id: str):
    reg = get_schema_registry()
    ok  = reg.delete(schema_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Schema '{schema_id}' not found")
    return TrishulResponse(success=True, data={"deleted": schema_id})
