"""Protobuf plugin settings."""
from pydantic_settings import BaseSettings


class ProtobufSettings(BaseSettings):
    PROTO_NATS_SUBJECT:  str = "fcaps.ingest.protobuf"
    PROTO_SIM_SUBJECT:   str = "fcaps.simulated.protobuf"
    PROTO_SCHEMA_ID:     str = "gnmi-v1"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_protobuf_settings() -> ProtobufSettings:
    return ProtobufSettings()
