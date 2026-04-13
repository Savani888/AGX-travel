from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AGX Tourism Engine", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(
        default="postgresql+psycopg2://agx:agx@localhost:5432/agx_tourism", alias="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    serp_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("SERP_API_KEY", "SERPAPI_API_KEY"),
    )
    serp_enabled: bool = Field(default=False, validation_alias="SERP_ENABLED")
    serp_fallback_min_results: int = Field(default=3, validation_alias="SERP_FALLBACK_MIN_RESULTS")
    serp_fallback_confidence_threshold: float = Field(
        default=0.6,
        validation_alias="SERP_FALLBACK_CONFIDENCE_THRESHOLD",
    )
    http_timeout_seconds: int = Field(default=8, alias="HTTP_TIMEOUT_SECONDS")
    enable_background_monitor: bool = Field(default=True, alias="ENABLE_BACKGROUND_MONITOR")


@lru_cache
def get_settings() -> Settings:
    return Settings()
