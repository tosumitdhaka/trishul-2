"""VESPlugin — FCAPSPlugin implementation."""
from core.plugin_registry import FCAPSPlugin
from plugins.ves.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.ves import VESDecoder


class VESPlugin(FCAPSPlugin):
    name    = "ves"
    version = "1.0.0"
    domains = ["FM", "PM", "LOG"]

    async def on_startup(self, app, nats, metrics_store, event_store) -> None:
        app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("ves", VESDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = VESPlugin()
