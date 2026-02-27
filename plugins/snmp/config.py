"""SNMP plugin settings."""
from pydantic_settings import BaseSettings


class SNMPSettings(BaseSettings):
    SNMP_TRAP_HOST:     str   = "0.0.0.0"
    SNMP_TRAP_PORT:     int   = 1162        # non-privileged mirror of UDP 162
    SNMP_COMMUNITY:     str   = "public"
    SNMP_VERSION:       str   = "v2c"
    SNMP_NATS_SUBJECT:  str   = "fcaps.ingest.snmp"
    SNMP_SIM_SUBJECT:   str   = "fcaps.simulated.snmp"

    model_config = {"env_file": ".env", "extra": "ignore"}


_settings: SNMPSettings | None = None


def get_snmp_settings() -> SNMPSettings:
    global _settings
    if _settings is None:
        _settings = SNMPSettings()
    return _settings
