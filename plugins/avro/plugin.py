"""AvroPlugin — FCAPSPlugin implementation."""
from core.plugin_registry import FCAPSPlugin
from plugins.avro.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.avro import AvroDecoder


class AvroPlugin(FCAPSPlugin):
    name    = "avro"
    version = "1.0.0"
    domains = ["PM", "LOG"]

    async def on_startup(self, app, nats, metrics_store, event_store) -> None:
        app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("avro", AvroDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = AvroPlugin()
