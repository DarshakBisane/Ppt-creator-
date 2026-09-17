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

    # Request Bounds & Slide Limits
    max_topic_chars: int = 1000
    max_audience_chars: int = 100
    max_purpose_chars: int = 100
    max_style_chars: int = 50
    min_slides: int = 3
    max_slides: int = 30

    # Reference PPTX & XML Security Limits
    max_reference_pptx_bytes: int = 50 * 1024 * 1024  # 50MB
    max_reference_unpacked_bytes: int = 50 * 1024 * 1024  # 50MB
    max_reference_files: int = 500
    max_reference_xml_bytes: int = 10 * 1024 * 1024  # 10MB

    # Concurrency & Job Lifecycle Limits
    max_job_runtime_seconds: int = 300  # 5 minutes
    max_concurrent_jobs: int = 5

    # Artifact Storage Configuration
    artifact_dir: str = "temp/artifacts"
    artifact_ttl_seconds: int = 3600
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50MB max upload

    # Docs / OpenAPI Exposure
    enable_docs: bool | None = None

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

    @property
    def show_docs(self) -> bool:
        """Determine whether API docs should be enabled."""
        if self.enable_docs is not None:
            return self.enable_docs
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

