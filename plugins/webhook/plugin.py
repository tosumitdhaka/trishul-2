"""WebhookPlugin — FCAPSPlugin implementation (promoted from Phase 1 scaffold)."""
from fastapi import APIRouter
from core.plugin_registry import FCAPSPlugin
from plugins.webhook.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.json import JSONDecoder


class WebhookPlugin(FCAPSPlugin):
    name      = "webhook"
    version   = "1.0.0"
    domains   = ["FM", "LOG"]
    protocols = ["webhook"]

    def get_router(self) -> APIRouter:
        return router

    def get_nats_subjects(self) -> list[str]:
        return ["fcaps.ingest.webhook", "fcaps.simulated.webhook"]

    def get_metadata(self) -> dict:
        return {"name": self.name, "version": self.version,
                "domains": self.domains, "protocols": self.protocols}

    async def on_startup(self, **kwargs) -> None:
        app = kwargs.get("app")
        if app:
            app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("json", JSONDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = WebhookPlugin()
