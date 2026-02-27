from typing import Any
from pydantic import BaseModel


class WebhookPayload(BaseModel):
    """Inbound webhook payload. Any JSON object is accepted."""
    source_ne:  str
    domain:     str = "LOG"           # FM | PM | LOG
    severity:   str | None = None     # required if domain=FM
    message:    str | None = None
    data:       dict[str, Any] = {}


class SimulateRequest(BaseModel):
    count:     int   = 1
    domain:    str   = "FM"
    source_ne: str   = "sim-ne-01"
    severity:  str   = "MAJOR"
