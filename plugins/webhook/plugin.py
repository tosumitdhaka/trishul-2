"""WebhookPlugin — FCAPSPlugin implementation for the Webhook reference plugin."""
from core.plugin_registry import FCAPSPlugin
from plugins.webhook.router import router


class WebhookPlugin(FCAPSPlugin):
    name     = "webhook"
    version  = "1.0.0"
    domains  = ["FM", "PM", "LOG"]
    protocols = ["webhook"]

    def get_router(self):
        return router

    def get_nats_subjects(self) -> list[str]:
        return ["fcaps.ingest.webhook", "fcaps.sim.webhook"]

    async def on_startup(self, **kwargs) -> None:
        from transformer.pipeline import pipeline_registry
        # Register JSONDecoder for 'webhook' protocol (Phase 2 will add real impl)
        # For Phase 1, we use the normalizer directly in the router
        import structlog
        structlog.get_logger(__name__).info("plugin_loaded", plugin=self.name, version=self.version)

    async def on_shutdown(self) -> None:
        pass

    def get_metadata(self) -> dict:
        return {
            "name":      self.name,
            "version":   self.version,
            "domains":   self.domains,
            "protocols": self.protocols,
        }


plugin = WebhookPlugin()
