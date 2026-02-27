"""SFTPPlugin — FCAPSPlugin implementation."""
from fastapi import APIRouter
from core.plugin_registry import FCAPSPlugin
from plugins.sftp.router import router
from transformer.pipeline import pipeline_registry
from transformer.readers.sftp import SFTPReader
from transformer.writers.sftp import SFTPWriter


class SFTPPlugin(FCAPSPlugin):
    name      = "sftp"
    version   = "1.0.0"
    domains   = ["PM", "LOG"]
    protocols = ["sftp"]

    def get_router(self) -> APIRouter:
        return router

    def get_nats_subjects(self) -> list[str]:
        from plugins.sftp.config import get_sftp_settings
        cfg = get_sftp_settings()
        return [cfg.SFTP_NATS_SUBJECT, cfg.SFTP_SIM_SUBJECT]

    def get_metadata(self) -> dict:
        return {"name": self.name, "version": self.version,
                "domains": self.domains, "protocols": self.protocols}

    async def on_startup(self, **kwargs) -> None:
        # Router registration is handled by PluginRegistry.load_all
        pipeline_registry.register_reader("sftp", SFTPReader())
        pipeline_registry.register_writer("sftp", SFTPWriter())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = SFTPPlugin()
