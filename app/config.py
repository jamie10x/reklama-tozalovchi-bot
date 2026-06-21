from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: str

    database_url: str = "postgresql+asyncpg://adcleaner:change_me@postgres:5432/adcleaner"
    secadmin_database_url: str = (
        "postgresql+asyncpg://secadmin_api:change_me@postgres:5432/adcleaner"
    )

    postgres_db: str = "adcleaner"
    postgres_user: str = "adcleaner"
    postgres_password: str = "change_me"

    log_level: str = "INFO"
    log_format: str = "json"
    bot_language: str = "uz"
    default_mode: str = "normal"
    deletion_log_retention_hours: int = 24
    cleanup_interval_minutes: int = 30
    message_excerpt_max_length: int = 250

    ai_enabled: bool = False
    ai_provider: str = "openai"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_api_url: str = ""

    def validate(self) -> None:
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        if self.default_mode not in ("relaxed", "normal", "strict"):
            raise ValueError(
                f"Invalid DEFAULT_MODE: {self.default_mode}. "
                "Must be one of: relaxed, normal, strict"
            )
        if self.deletion_log_retention_hours < 1:
            raise ValueError("DELETION_LOG_RETENTION_HOURS must be at least 1")
        if self.cleanup_interval_minutes < 1:
            raise ValueError("CLEANUP_INTERVAL_MINUTES must be at least 1")


def load_config() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
