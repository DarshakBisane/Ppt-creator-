"""Tests for configuration parsing and environments."""

from backend.app.config import Settings


def test_default_settings() -> None:
    """Verify default settings values."""
    settings = Settings(
        app_name="AI Presentation Generator",
        environment="development",
    )
    assert settings.app_name == "AI Presentation Generator"
    assert settings.environment == "development"
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.is_test is False


def test_cors_origins_parsing_from_string() -> None:
    """Verify comma-separated string is parsed into list of origins."""
    settings = Settings(
        cors_origins="http://example.com, http://localhost:3000,http://app.internal"
    )
    assert settings.cors_origins == [
        "http://example.com",
        "http://localhost:3000",
        "http://app.internal",
    ]


def test_cors_origins_parsing_from_list() -> None:
    """Verify list of origins is preserved."""
    origins = ["http://frontend.local:5173", "http://localhost:8000"]
    settings = Settings(cors_origins=origins)
    assert settings.cors_origins == origins


def test_environment_flags() -> None:
    """Verify environment property flags."""
    prod = Settings(environment="production")
    assert prod.is_production is True
    assert prod.is_development is False
    assert prod.is_test is False

    test_env = Settings(environment="test")
    assert test_env.is_test is True
    assert test_env.is_production is False
