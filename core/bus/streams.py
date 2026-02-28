"""JetStream stream provisioner — idempotent, runs at startup."""
from nats.js.errors import BadRequestError
from nats.aio.client import Client as NATSClient

from core.bus.client import TrishulNATSClient

STREAM_CONFIGS = [
    {
        "name":     "FCAPS_INGEST",
        "subjects": ["fcaps.ingest.>"],
        "storage":  "file",
        "max_age":  3600,
        "retention": "limits",
    },
    {
        "name":     "FCAPS_PROCESS",
        "subjects": ["fcaps.process.>"],
        "storage":  "memory",
        "retention": "workqueue",
    },
    {
        "name":     "FCAPS_DONE",
        "subjects": ["fcaps.done.>"],
        "storage":  "memory",
        "max_age":  1800,
        "retention": "limits",
    },
    {
        "name":     "FCAPS_SIM",
        # All plugin simulate endpoints publish to fcaps.simulated.<protocol>
        # Previously this was fcaps.sim.> which caused NoStreamResponseError.
        "subjects": ["fcaps.simulated.>"],
        "storage":  "memory",
        "max_age":  3600,
        "retention": "limits",
    },
]


async def provision_streams(nats_client: TrishulNATSClient) -> None:
    """Create or update all streams. Safe to call on every startup."""
    import structlog
    log = structlog.get_logger(__name__)
    js  = nats_client.js

    for cfg in STREAM_CONFIGS:
        try:
            await js.add_stream(
                name=cfg["name"],
                subjects=cfg["subjects"],
            )
            log.info("stream_created", stream=cfg["name"])
        except BadRequestError:
            # Stream exists — update it so subject changes take effect
            try:
                await js.update_stream(
                    name=cfg["name"],
                    subjects=cfg["subjects"],
                )
                log.info("stream_updated", stream=cfg["name"])
            except Exception as update_err:
                log.warning("stream_update_skipped", stream=cfg["name"], error=str(update_err))
