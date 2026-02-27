"""Central settings via pydantic-settings — single source of truth for all config."""
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_ENV:      Literal["lab", "prod"] = "lab"
    LOG_LEVEL:    str = "INFO"
    STORAGE_MODE: Literal["lab", "prod"] = "lab"

    # Auth
    JWT_SECRET:             str
    JWT_ACCESS_TTL_MINUTES: int  = 15
    JWT_REFRESH_TTL_DAYS:   int  = 7
    RATE_LIMIT_DEFAULT:     int  = 60
    RATE_LIMIT_PLUGIN:      int  = 600

    # NATS
    NATS_URL: str = "nats://nats:4222"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # InfluxDB
    INFLUX_URL:    str
    INFLUX_TOKEN:  str
    INFLUX_ORG:    str = "trishul"
    INFLUX_BUCKET: str = "fcaps_pm"

    # VictoriaLogs
    VICTORIA_URL: str = "http://victorialogs:9428"

    # SQLite
    SQLITE_PATH: str = "/data/fcaps.db"

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
