"""VictoriaLogsWriter — pushes JSON-encoded envelope to VictoriaLogs."""
from transformer.base import Writer


class VictoriaLogsWriter(Writer):
    target = "victorialogs"

    def __init__(self, event_store) -> None:
        self._store = event_store

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        from core.models.envelope import MessageEnvelope, FCAPSDomain

        if isinstance(data, (bytes, bytearray)):
            envelope_dict = json.loads(data.decode("utf-8"))
        else:
            envelope_dict = data

        envelope = MessageEnvelope.model_validate(envelope_dict)

        # domain may deserialise as str (enum value) or FCAPSDomain enum
        domain = envelope.domain
        domain_str = domain.value if isinstance(domain, FCAPSDomain) else str(domain)

        if domain_str == "FM":
            await self._store.write_fm(envelope)
        else:
            await self._store.write_log(envelope)
