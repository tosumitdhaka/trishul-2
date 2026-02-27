"""Pydantic models for SNMP plugin endpoints."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class VarBind(BaseModel):
    oid:   str
    value: Any


class SNMPTrapRequest(BaseModel):
    agent_address: str           = Field(..., json_schema_extra={"example": "192.168.1.1"})
    community:     str           = Field("public")
    version:       str           = Field("v2c")
    trap_oid:      str           = Field(..., json_schema_extra={"example": "1.3.6.1.6.3.1.1.5.3"})
    varbinds:      list[VarBind] = Field(default_factory=list)
    severity:      str | None    = None


class SNMPSimulateRequest(BaseModel):
    count:      int  = Field(1, ge=1, le=100)
    trap_type:  str  = Field("linkDown")
    source_ne:  str  = Field("sim-ne-01")
    domain:     str  = Field("FM")


class SNMPSendRequest(BaseModel):
    target_host: str
    target_port: int            = 162
    community:   str            = "public"
    trap_oid:    str
    varbinds:    list[VarBind]  = Field(default_factory=list)
