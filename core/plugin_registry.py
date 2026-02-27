"""FCAPSPlugin ABC + PluginRegistry singleton with auto-discovery."""
from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fastapi import FastAPI
import structlog

if TYPE_CHECKING:
    from core.bus.client import TrishulNATSClient
    from core.storage.base import MetricsStore, EventStore

log = structlog.get_logger(__name__)

# Subpackages that are NOT plugins (utilities, shared code, etc.)
_NON_PLUGIN_MODULES = {"shared"}


class FCAPSPlugin(ABC):
    """Every protocol plugin must subclass this and expose a module-level `plugin` instance."""

    name:      str
    version:   str
    domains:   list[str]
    protocols: list[str]

    @abstractmethod
    def get_router(self):
        """Return the FastAPI APIRouter for this plugin."""
        ...

    @abstractmethod
    def get_nats_subjects(self) -> list[str]:
        """Return list of NATS subjects this plugin publishes to."""
        ...

    @abstractmethod
    async def on_startup(self, **kwargs) -> None:
        """Called during app startup after NATS + storage are ready."""
        ...

    @abstractmethod
    async def on_shutdown(self) -> None:
        """Called during graceful shutdown."""
        ...

    @abstractmethod
    def get_metadata(self) -> dict:
        """Return plugin metadata dict for registry endpoint."""
        ...


class PluginRegistry:
    """Singleton registry: auto-discovers all plugins in the `plugins/` package."""

    def __init__(self) -> None:
        self.plugins: dict[str, FCAPSPlugin] = {}

    async def load_all(
        self,
        app:           FastAPI,
        nats_client,
        metrics_store,
        event_store,
    ) -> None:
        """Auto-discover, load, and register all plugins."""
        import plugins as plugins_pkg

        for module_info in pkgutil.iter_modules(plugins_pkg.__path__):
            if module_info.name in _NON_PLUGIN_MODULES:
                log.debug("plugin_skipped_non_plugin", module=module_info.name)
                continue

            module_name = f"plugins.{module_info.name}"
            try:
                module = importlib.import_module(module_name)

                if not hasattr(module, "plugin"):
                    log.warning("plugin_missing_instance", module=module_name)
                    continue

                plugin: FCAPSPlugin = module.plugin

                await plugin.on_startup(
                    nats=nats_client,
                    metrics_store=metrics_store,
                    event_store=event_store,
                )

                app.include_router(
                    plugin.get_router(),
                    prefix=f"/api/v1/{plugin.name}",
                )

                self.plugins[plugin.name] = plugin
                log.info("plugin_loaded", plugin=plugin.name, version=plugin.version)

            except Exception as exc:
                log.error(
                    "plugin_startup_failed",
                    module=module_name,
                    error=str(exc),
                    exc_info=True,
                )

    async def shutdown_all(self) -> None:
        for plugin in self.plugins.values():
            try:
                await plugin.on_shutdown()
            except Exception as exc:
                log.error("plugin_shutdown_error", plugin=plugin.name, error=str(exc))
