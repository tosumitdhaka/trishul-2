"""SNMPPlugin — FCAPSPlugin implementation."""
from core.plugin_registry import FCAPSPlugin
from plugins.snmp.router import router
from plugins.snmp.pipeline import build_snmp_pipeline
from transformer.pipeline import pipeline_registry
from transformer.decoders.snmp import SNMPDecoder


class SNMPPlugin(FCAPSPlugin):
    name    = "snmp"
    version = "1.0.0"
    domains = ["FM", "PM"]

    async def on_startup(self, app, nats, metrics_store, event_store) -> None:
        app.include_router(router, prefix="/api/v1")
        # Register SNMP decoder with global pipeline registry
        pipeline_registry.register_decoder("snmp", SNMPDecoder())
        from transformer.writers.victorialogs import VictoriaLogsWriter
        from transformer.writers.webhook import WebhookWriter
        pipeline_registry.register_writer("webhook", WebhookWriter())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = SNMPPlugin()
