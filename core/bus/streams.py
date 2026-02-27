"""JetStream stream provisioning.

All four streams are created at startup if they don't already exist.
Existing streams with matching configs are left untouched (idempotent).
"""

import logging

from nats.js import JetStreamContext
from nats.js.api import RetentionPolicy, StorageType, StreamConfig

log = logging.getLogger(__name__)

STREAMS: list[StreamConfig] = [
    StreamConfig(
        name="FCAPS_INGEST",
        subjects=["fcaps.ingest.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        max_age=3600,           # 1 hour
        description="Raw inbound messages — survives restart",
    ),
    StreamConfig(
        name="FCAPS_PROCESS",
        subjects=["fcaps.process.>"],
        storage=StorageType.MEMORY,
        retention=RetentionPolicy.WORK_QUEUE,
        description="Transformer work queue — once-and-only-once processing",
    ),
    StreamConfig(
        name="FCAPS_DONE",
        subjects=["fcaps.done.>"],
        storage=StorageType.MEMORY,
        retention=RetentionPolicy.LIMITS,
        max_age=1800,           # 30 minutes
        description="Processed envelopes — fan-out to storage + websocket",
    ),
    StreamConfig(
        name="FCAPS_SIM",
        subjects=["fcaps.sim.>"],
        storage=StorageType.MEMORY,
        retention=RetentionPolicy.LIMITS,
        max_age=3600,           # 1 hour
        description="Simulated outbound messages — audit trail",
    ),
]


async def provision(js: JetStreamContext) -> None:
    """Idempotently create all FCAPS streams."""
    for cfg in STREAMS:
        try:
            await js.find_stream(cfg.name)
            log.info("nats_stream_exists", extra={"stream": cfg.name})
        except Exception:
            await js.add_stream(cfg)
            log.info("nats_stream_created", extra={"stream": cfg.name})
