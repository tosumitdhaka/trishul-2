"""SNMPPlugin — FCAPSPlugin implementation."""
from fastapi import APIRouter
from core.plugin_registry import FCAPSPlugin
from plugins.snmp.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.snmp import SNMPDecoder


class SNMPPlugin(FCAPSPlugin):
    name      = "snmp"
    version   = "1.0.0"
    domains   = ["FM", "PM"]
    protocols = ["snmp"]

    def get_router(self) -> APIRouter:
        return router

    def get_nats_subjects(self) -> list[str]:
        from plugins.snmp.config import get_snmp_settings
        cfg = get_snmp_settings()
        return [cfg.SNMP_NATS_SUBJECT, cfg.SNMP_SIM_SUBJECT]

    def get_metadata(self) -> dict:
        return {"name": self.name, "version": self.version,
                "domains": self.domains, "protocols": self.protocols}

    async def on_startup(self, **kwargs) -> None:
        app = kwargs.get("app")
        if app:
            app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("snmp", SNMPDecoder())
        from transformer.writers.webhook import WebhookWriter
        pipeline_registry.register_writer("webhook", WebhookWriter())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = SNMPPlugin()
