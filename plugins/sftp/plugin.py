"""SFTPPlugin — FCAPSPlugin implementation."""
from core.plugin_registry import FCAPSPlugin
from plugins.sftp.router import router
from transformer.pipeline import pipeline_registry
from transformer.readers.sftp import SFTPReader
from transformer.writers.sftp import SFTPWriter


class SFTPPlugin(FCAPSPlugin):
    name    = "sftp"
    version = "1.0.0"
    domains = ["PM", "LOG"]

    async def on_startup(self, app, nats, metrics_store, event_store) -> None:
        app.include_router(router, prefix="/api/v1")
        pipeline_registry.register_reader("sftp", SFTPReader())
        pipeline_registry.register_writer("sftp", SFTPWriter())

    async def on_shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"plugin": self.name, "status": "healthy"}


plugin = SFTPPlugin()
