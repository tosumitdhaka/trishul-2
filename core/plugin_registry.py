"""Plugin system — FCAPSPlugin ABC + PluginRegistry singleton.

At startup, PluginRegistry.load_all() scans the plugins/ package,
imports each sub-package, retrieves the module-level `plugin` instance,
calls on_startup(), and registers its FastAPI router with the app.

Every new protocol is a drop-in: create plugins/{name}/ with __init__.py
exporting plugin = MyPlugin(). Core never needs modification.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod

import plugins as plugins_pkg
from fastapi import APIRouter, FastAPI

log = logging.getLogger(__name__)


class FCAPSPlugin(ABC):
    """Base class every protocol plugin must subclass."""

    name:     str   # e.g. "webhook"
    version:  str   # e.g. "1.0.0"
    domains:  list[str]   # e.g. ["FM", "LOG"]
    protocols: list[str]  # e.g. ["webhook"]

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return the FastAPI router to be mounted at /api/v1/{name}/."""

    @abstractmethod
    def get_nats_subjects(self) -> list[str]:
        """Return NATS subjects this plugin publishes to."""

    @abstractmethod
    async def on_startup(self, app: FastAPI) -> None:
        """Called once at app startup. Wire pipeline stages here."""

    @abstractmethod
    async def on_shutdown(self) -> None:
        """Called once at app shutdown. Release plugin resources."""

    def get_metadata(self) -> dict:
        return {
            "name":      self.name,
            "version":   self.version,
            "domains":   self.domains,
            "protocols": self.protocols,
            "subjects":  self.get_nats_subjects(),
        }


class PluginRegistry:
    """Discovers, loads, and tracks all protocol plugins."""

    def __init__(self) -> None:
        self.plugins: dict[str, FCAPSPlugin] = {}

    async def load_all(self, app: FastAPI) -> None:
        """Auto-discover and load all plugins from the plugins/ package."""
        for module_info in pkgutil.iter_modules(plugins_pkg.__path__):
            module_name = f"plugins.{module_info.name}"
            try:
                mod    = importlib.import_module(module_name)
                plugin: FCAPSPlugin = mod.plugin

                await plugin.on_startup(app)

                app.include_router(
                    plugin.get_router(),
                    prefix=f"/api/v1/{plugin.name}",
                )

                self.plugins[plugin.name] = plugin
                log.info("plugin_loaded", extra={
                    "plugin":  plugin.name,
                    "version": plugin.version,
                })
            except Exception as exc:
                log.error("plugin_startup_failed", extra={
                    "module": module_name,
                    "error":  str(exc),
                })
                raise

    async def shutdown_all(self) -> None:
        for plugin in self.plugins.values():
            await plugin.on_shutdown()

    def get_registry_list(self) -> list[dict]:
        return [p.get_metadata() for p in self.plugins.values()]
