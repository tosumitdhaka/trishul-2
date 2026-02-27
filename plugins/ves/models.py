"""Pydantic models for VES plugin endpoints."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class VESEventRequest(BaseModel):
    event: dict = Field(..., description="VES CommonEventFormat event object")


class VESSimulateRequest(BaseModel):
    count:     int  = Field(1, ge=1, le=100)
    domain:    str  = Field("fault")
    severity:  str  = Field("CRITICAL")
    source_ne: str  = Field("sim-ems-01")
