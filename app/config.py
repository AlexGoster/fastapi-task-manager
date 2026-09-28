"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FastAPI Task Manager"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/taskdb"

    secret_key: str = "dev-secret-key-change-me-in-production-32b"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    log_level: str = "INFO"

    @property
    def database_sync_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
