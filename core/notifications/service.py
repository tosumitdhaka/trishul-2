"""NotificationService — NATS consumer for all fcaps.* subjects that fans out to storage + WebSocket.

Subject coverage:
  fcaps.done.>       — intended final processed output (future)
  fcaps.ingest.>     — currently where pipeline outputs land for receive endpoints
  fcaps.simulated.>  — where simulate endpoints publish

All three carry serialised MessageEnvelope JSON so we can treat them identically.
"""
import json
import structlog

from core.models.envelope import MessageEnvelope, FCAPSDomain

log = structlog.get_logger(__name__)

# All NATS subjects whose messages should fan-out to storage + WebSocket.
# The pipeline already normalises raw data into MessageEnvelope before publishing
# to any of these subjects, so all three carry the same schema.
_SUBJECTS = [
    "fcaps.done.>",
    "fcaps.ingest.>",
    "fcaps.simulated.>",
]


class NotificationService:
    """Subscribes to all fcaps subject trees and dispatches to:
    1. Storage writers (InfluxDB / VictoriaLogs)
    2. WebSocket broadcaster → connected browsers
    """

    def __init__(self, nats_client, metrics_store, event_store) -> None:
        self._nats          = nats_client
        self._metrics_store = metrics_store
        self._event_store   = event_store
        self._subs          = []

    async def start(self) -> None:
        for subject in _SUBJECTS:
            sub = await self._nats.nc.subscribe(
                subject,
                cb=self._handle,
                queue="storage-writer",
            )
            self._subs.append(sub)
        log.info("notification_service_started", subjects=_SUBJECTS)

    async def stop(self) -> None:
        for sub in self._subs:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        self._subs.clear()
        log.info("notification_service_stopped")

    async def _handle(self, msg) -> None:
        try:
            data     = json.loads(msg.data.decode())
            envelope = MessageEnvelope.model_validate(data)

            # Route to the correct storage backend by FCAPS domain
            if envelope.domain == FCAPSDomain.PM:
                await self._metrics_store.write_pm(envelope)
            elif envelope.domain == FCAPSDomain.FM:
                await self._event_store.write_fm(envelope)
            elif envelope.domain == FCAPSDomain.LOG:
                await self._event_store.write_log(envelope)

            log.info(
                "envelope_stored",
                envelope_id=envelope.id,
                domain=envelope.domain.value,
                subject=msg.subject,
            )

            # Broadcast to WebSocket clients
            try:
                from core.ws.router import broadcast_envelope
                await broadcast_envelope(data)
            except Exception as ws_exc:
                log.warning("ws_broadcast_failed", error=str(ws_exc))

        except Exception as exc:
            log.error("storage_write_failed", error=str(exc), exc_info=True)
