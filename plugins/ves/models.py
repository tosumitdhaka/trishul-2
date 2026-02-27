"""Pydantic models for VES plugin endpoints."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class VESEventRequest(BaseModel):
    """Full VES 7.x CommonEventFormat wrapper."""
    event: dict = Field(..., description="VES CommonEventFormat event object")


class VESSimulateRequest(BaseModel):
    count:      int  = Field(1, ge=1, le=100)
    domain:     str  = Field("fault",     example="fault")
    severity:   str  = Field("CRITICAL",  example="CRITICAL")
    source_ne:  str  = Field("sim-ems-01")
