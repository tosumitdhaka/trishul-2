"""VictoriaLogsWriter — pushes JSON-encoded envelope to VictoriaLogs."""
from transformer.base import Writer


class VictoriaLogsWriter(Writer):
    target = "victorialogs"

    def __init__(self, event_store) -> None:
        self._store = event_store

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        from core.models.envelope import MessageEnvelope

        if isinstance(data, (bytes, bytearray)):
            envelope_dict = json.loads(data.decode("utf-8"))
        else:
            envelope_dict = data

        envelope = MessageEnvelope.model_validate(envelope_dict)
        domain   = envelope.domain.value

        if domain == "FM":
            await self._store.write_fm(envelope)
        else:
            await self._store.write_log(envelope)
