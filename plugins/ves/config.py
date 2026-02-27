"""VES plugin settings."""
from pydantic_settings import BaseSettings


class VESSettings(BaseSettings):
    VES_NATS_SUBJECT: str = "fcaps.ingest.ves"
    VES_SIM_SUBJECT:  str = "fcaps.simulated.ves"

    model_config = {"env_file": ".env", "extra": "ignore"}


_settings: VESSettings | None = None


def get_ves_settings() -> VESSettings:
    global _settings
    if _settings is None:
        _settings = VESSettings()
    return _settings
