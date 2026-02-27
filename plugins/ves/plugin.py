"""VESPlugin — FCAPSPlugin implementation."""
from fastapi import APIRouter
from core.plugin_registry import FCAPSPlugin
from plugins.ves.router import router
from transformer.pipeline import pipeline_registry
from transformer.decoders.ves import VESDecoder


class VESPlugin(FCAPSPlugin):
    name      = "ves"
    version   = "1.0.0"
    domains   = ["FM", "PM", "LOG"]
    protocols = ["ves"]

    def get_router(self) -> APIRouter:
        return router

    def get_nats_subjects(self) -> list[str]:
        from plugins.ves.config import get_ves_settings
        cfg = get_ves_settings()
        return [cfg.VES_NATS_SUBJECT, cfg.VES_SIM_SUBJECT]

    def get_metadata(self) -> dict:
        return {"name": self.name, "version": self.version,
                "domains": self.domains, "protocols": self.protocols}

    async def on_startup(self, **kwargs) -> None:
        app = kwargs.get("app")
        if app:
            app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_decoder("ves", VESDecoder())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = VESPlugin()
