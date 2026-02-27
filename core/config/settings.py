from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = Field(default="lab", description="lab | prod")
    app_version: str = Field(default="1.0.0")
    log_level: str = Field(default="INFO")
    storage_mode: str = Field(default="lab", description="lab | prod")

    # JWT
    jwt_secret: str = Field(..., description="HS256 signing secret, min 32 chars")
    jwt_access_ttl_minutes: int = Field(default=15)
    jwt_refresh_ttl_days: int = Field(default=7)

    # Rate limiting
    rate_limit_default: int = Field(default=60, description="req/min for regular clients")
    rate_limit_plugin: int = Field(default=600, description="req/min for plugin API keys")

    # NATS
    nats_url: str = Field(default="nats://nats:4222")

    # Redis
    redis_url: str = Field(default="redis://redis:6379")

    # InfluxDB
    influx_url: str = Field(default="http://influxdb:8086")
    influx_token: str = Field(...)
    influx_org: str = Field(default="trishul")
    influx_bucket: str = Field(default="fcaps_pm")

    # VictoriaLogs
    victoria_url: str = Field(default="http://victorialogs:9428")

    # SQLite
    sqlite_path: str = Field(default="/data/fcaps.db")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
