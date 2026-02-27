"""InfluxDBWriter — writes line protocol bytes to InfluxDB v2."""
from transformer.base import Writer


class InfluxDBWriter(Writer):
    """sink_config keys: bucket (optional, defaults to settings)."""
    target = "influxdb"

    def __init__(self, metrics_store) -> None:
        self._store = metrics_store

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        # data is JSON-encoded envelope bytes from JSONEncoder
        import json
        from core.models.envelope import MessageEnvelope

        if isinstance(data, (bytes, bytearray)):
            envelope_dict = json.loads(data.decode("utf-8"))
        else:
            envelope_dict = data

        envelope = MessageEnvelope.model_validate(envelope_dict)
        await self._store.write_pm(envelope)
