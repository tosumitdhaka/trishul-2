"""Webhook protocol plugin — reference implementation for Phase 1.

Demonstrates the complete plugin contract:
  - FCAPSPlugin subclass
  - 5 standard endpoints (receive, send, simulate, status, health)
  - Ingest → NATS → 202 flow
  - Decoder registered with PipelineRegistry
  - FCAPSNormalizer used for envelope creation
"""

from plugins.webhook.plugin import WebhookPlugin

plugin = WebhookPlugin()
