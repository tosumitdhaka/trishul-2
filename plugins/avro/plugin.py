"""AvroPlugin — FCAPSPlugin implementation."""
from fastapi import APIRouter
from core.plugin_registry import FCAPSPlugin
from plugins.avro.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.avro import AvroDecoder


class AvroPlugin(FCAPSPlugin):
    name      = "avro"
    version   = "1.0.0"
    domains   = ["PM", "LOG"]
    protocols = ["avro"]

    def get_router(self) -> APIRouter:
        return router

    def get_nats_subjects(self) -> list[str]:
        from plugins.avro.config import get_avro_settings
        cfg = get_avro_settings()
        return [cfg.AVRO_NATS_SUBJECT, cfg.AVRO_SIM_SUBJECT]

    def get_metadata(self) -> dict:
        return {"name": self.name, "version": self.version,
                "domains": self.domains, "protocols": self.protocols}

    async def on_startup(self, **kwargs) -> None:
        app = kwargs.get("app")
        if app:
            app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("avro", AvroDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = AvroPlugin()
