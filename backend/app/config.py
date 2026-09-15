"""Application configuration settings."""

from functools import lru_cache
from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated via Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Presentation Generator"
    environment: Literal["development", "test", "production"] = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Gemini AI Configuration
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ai_timeout_seconds: float = 60.0
    ai_max_attempts: int = 2

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Parse comma-separated string or list of origins."""
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:5173"]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
