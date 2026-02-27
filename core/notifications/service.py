"""NotificationService — NATS fcaps.done.> consumer that fans out to storage + WebSocket."""
import json
import structlog

from core.models.envelope import MessageEnvelope, FCAPSDomain

log = structlog.get_logger(__name__)


class NotificationService:
    """Subscribes to fcaps.done.> and dispatches to:
    1. Storage writers (InfluxDB / VictoriaLogs)
    2. WebSocket broadcaster → connected browsers (Phase 4+)
    """

    def __init__(self, nats_client, metrics_store, event_store) -> None:
        self._nats          = nats_client
        self._metrics_store = metrics_store
        self._event_store   = event_store
        self._sub           = None

    async def start(self) -> None:
        self._sub = await self._nats.nc.subscribe(
            "fcaps.done.>",
            cb=self._handle,
            queue="storage-writer",
        )
        log.info("notification_service_started")

    async def stop(self) -> None:
        if self._sub:
            await self._sub.unsubscribe()
        log.info("notification_service_stopped")

    async def _handle(self, msg) -> None:
        try:
            data     = json.loads(msg.data.decode())
            envelope = MessageEnvelope.model_validate(data)

            # 1. Storage writes
            if envelope.domain == FCAPSDomain.PM:
                await self._metrics_store.write_pm(envelope)
            elif envelope.domain == FCAPSDomain.FM:
                await self._event_store.write_fm(envelope)
            elif envelope.domain == FCAPSDomain.LOG:
                await self._event_store.write_log(envelope)

            log.info("envelope_stored", envelope_id=envelope.id, domain=envelope.domain.value)

            # 2. WebSocket broadcast → all connected browser clients
            try:
                from core.ws.router import broadcast_envelope
                await broadcast_envelope(data)
            except Exception as ws_exc:
                # Never let WS errors kill the storage write path
                log.warning("ws_broadcast_failed", error=str(ws_exc))

        except Exception as exc:
            log.error("storage_write_failed", error=str(exc), exc_info=True)
