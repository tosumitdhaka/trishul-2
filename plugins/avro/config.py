"""Avro plugin settings."""
from pydantic_settings import BaseSettings


class AvroSettings(BaseSettings):
    AVRO_NATS_SUBJECT: str = "fcaps.ingest.avro"
    AVRO_SIM_SUBJECT:  str = "fcaps.simulated.avro"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_avro_settings() -> AvroSettings:
    return AvroSettings()
