from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="API_",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me-in-production"
    session_ttl_hours: int = 24
    debug: bool = False


def load_api_config() -> ApiSettings:
    return ApiSettings()
