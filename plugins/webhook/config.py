"""Webhook plugin settings — extends core BaseSettings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebhookSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="ignore", case_sensitive=True,
    )
    WEBHOOK_MAX_PAYLOAD_BYTES: int = 1_048_576  # 1 MB
    WEBHOOK_DEFAULT_DOMAIN:    str = "FM"


@lru_cache(maxsize=1)
def get_webhook_settings() -> WebhookSettings:
    return WebhookSettings()
