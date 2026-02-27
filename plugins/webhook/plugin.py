"""WebhookPlugin — concrete FCAPSPlugin implementation.

Registers JSONDecoder with PipelineRegistry at startup.
All inbound data is treated as JSON (most flexible for a webhook).
"""

from fastapi import APIRouter, FastAPI

from core.plugin_registry import FCAPSPlugin
from transformer.pipeline import pipeline_registry


class WebhookPlugin(FCAPSPlugin):
    name      = "webhook"
    version   = "1.0.0"
    domains   = ["FM", "PM", "LOG"]
    protocols = ["webhook"]

    def get_router(self) -> APIRouter:
        from plugins.webhook.router import router
        return router

    def get_nats_subjects(self) -> list[str]:
        return ["fcaps.ingest.webhook"]

    async def on_startup(self, app: FastAPI) -> None:
        # Register JSONDecoder for 'webhook' format
        # JSONDecoder is a Phase 2 impl; here we inline a minimal one
        from transformer.base import Decoder
        from transformer.normalizer import FCAPSNormalizer

        class _InlineJSONDecoder(Decoder):
            format = "json"
            async def decode(self, raw: bytes | dict) -> dict:
                if isinstance(raw, bytes):
                    import json
                    return json.loads(raw)
                return raw

        pipeline_registry.register_decoder("webhook", _InlineJSONDecoder())
        pipeline_registry.set_normalizer(FCAPSNormalizer())

    async def on_shutdown(self) -> None:
        pass
