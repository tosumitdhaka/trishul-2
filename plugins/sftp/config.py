"""SFTP plugin settings."""
from pydantic_settings import BaseSettings


class SFTPSettings(BaseSettings):
    SFTP_HOST:         str       = "localhost"
    SFTP_PORT:         int       = 22
    SFTP_USERNAME:     str       = "trishul"
    SFTP_PASSWORD:     str       = ""
    SFTP_KEY_PATH:     str       = ""
    SFTP_POLL_PATH:    str       = "/ingest/"
    SFTP_NATS_SUBJECT: str       = "fcaps.ingest.sftp"
    SFTP_SIM_SUBJECT:  str       = "fcaps.simulated.sftp"

    model_config = {"env_file": ".env", "extra": "ignore"}


def get_sftp_settings() -> SFTPSettings:
    return SFTPSettings()
