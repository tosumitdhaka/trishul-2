"""ProtobufPlugin — FCAPSPlugin implementation."""
from core.plugin_registry import FCAPSPlugin
from plugins.protobuf.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.protobuf import ProtobufDecoder


class ProtobufPlugin(FCAPSPlugin):
    name    = "protobuf"
    version = "1.0.0"
    domains = ["PM"]

    async def on_startup(self, app, nats, metrics_store, event_store) -> None:
        app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("protobuf", ProtobufDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = ProtobufPlugin()
