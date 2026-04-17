"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend application."""

    app_name: str = "Notification API"
    app_env: str = "development"
    api_prefix: str = "/v1"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/notifications"
    )
    frontend_app_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def cors_origin_list(self) -> list[str]:
        """Parse a comma-separated CORS origin list into individual origins."""

        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Cache settings so they are loaded once per process."""

    return Settings()


settings = get_settings()
