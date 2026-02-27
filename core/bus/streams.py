"""JetStream stream provisioner — idempotent, runs at startup."""
from nats.js.errors import BadRequestError

from core.bus.client import TrishulNATSClient

STREAM_CONFIGS = [
    {
        "name":     "FCAPS_INGEST",
        "subjects": ["fcaps.ingest.>"],
        "storage":  "file",
        "max_age":  3600,          # 1 hour in seconds
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
        "max_age":  1800,          # 30 minutes
        "retention": "limits",
    },
    {
        "name":     "FCAPS_SIM",
        "subjects": ["fcaps.sim.>"],
        "storage":  "memory",
        "max_age":  3600,
        "retention": "limits",
    },
]


async def provision_streams(nats_client: TrishulNATSClient) -> None:
    """Create all 4 streams if they don't exist. Safe to call on every startup."""
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
            log.debug("stream_exists", stream=cfg["name"])
