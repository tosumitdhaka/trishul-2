"""Pydantic models for Webhook plugin request/response."""
from typing import Any, Optional
from pydantic import BaseModel


class WebhookPayload(BaseModel):
    """Inbound webhook payload."""
    source_ne:  str
    domain:     str = "FM"           # FM | PM | LOG
    protocol:   str = "webhook"
    severity:   Optional[str] = None
    message:    Optional[str] = None
    data:       dict[str, Any] = {}


class SimulateRequest(BaseModel):
    count:    int   = 5
    domain:   str   = "FM"
    severity: str   = "MAJOR"
    source_ne: str  = "sim-ne-01"


class SendRequest(BaseModel):
    target_url: str
    payload:    dict[str, Any]
