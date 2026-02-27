from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["lab", "prod"] = "lab"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    storage_mode: Literal["lab", "prod"] = "lab"
    app_version: str = "1.0.0"

    # Auth
    jwt_secret: str
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    rate_limit_default: int = 60   # req/min
    rate_limit_plugin: int = 600   # req/min for plugin API keys

    # NATS
    nats_url: str = "nats://nats:4222"

    # Redis
    redis_url: str = "redis://redis:6379"

    # InfluxDB
    influx_url: str = "http://influxdb:8086"
    influx_token: str
    influx_org: str = "trishul"
    influx_bucket: str = "fcaps_pm"

    # VictoriaLogs
    victoria_url: str = "http://victorialogs:9428"

    # SQLite
    sqlite_path: str = "/data/fcaps.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance. Call once at startup, reuse everywhere."""
    return Settings()
