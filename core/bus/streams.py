from __future__ import annotations

import logging

from nats.aio.client import Client as NATSClient
from nats.js.api import RetentionPolicy, StorageType, StreamConfig

log = logging.getLogger(__name__)

# Stream definitions — frozen per architecture doc
_STREAMS: list[dict] = [
    {
        "name":     "FCAPS_INGEST",
        "subjects": ["fcaps.ingest.>"],
        "storage":  StorageType.FILE,
        "retention": RetentionPolicy.LIMITS,
        "max_age":  3600,   # 1 hour in seconds
    },
    {
        "name":     "FCAPS_PROCESS",
        "subjects": ["fcaps.process.>"],
        "storage":  StorageType.MEMORY,
        "retention": RetentionPolicy.WORK_QUEUE,
        "max_age":  0,
    },
    {
        "name":     "FCAPS_DONE",
        "subjects": ["fcaps.done.>"],
        "storage":  StorageType.MEMORY,
        "retention": RetentionPolicy.LIMITS,
        "max_age":  1800,   # 30 minutes
    },
    {
        "name":     "FCAPS_SIM",
        "subjects": ["fcaps.sim.>"],
        "storage":  StorageType.MEMORY,
        "retention": RetentionPolicy.LIMITS,
        "max_age":  3600,
    },
]


async def provision_streams(nc: NATSClient) -> None:
    """Idempotent — creates streams if they don't exist."""
    js = nc.jetstream()
    for cfg in _STREAMS:
        stream_cfg = StreamConfig(
            name=cfg["name"],
            subjects=cfg["subjects"],
            storage=cfg["storage"],
            retention=cfg["retention"],
            max_age=cfg["max_age"],
        )
        try:
            await js.find_stream(cfg["subjects"][0])
            log.info("event=stream_exists name=%s", cfg["name"])
        except Exception:
            await js.add_stream(stream_cfg)
            log.info("event=stream_created name=%s", cfg["name"])
