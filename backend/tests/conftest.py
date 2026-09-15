"""Shared test fixtures."""

import os
import pytest
from collections.abc import Generator
from fastapi.testclient import TestClient

# Ensure test environment by default
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"

from backend.app.config import Settings
from backend.app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated test settings."""
    return Settings(
        app_name="Test Presentation Generator",
        environment="test",
        cors_origins=["http://localhost:5173", "http://testserver"],
        log_level="DEBUG",
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Fixture providing configured TestClient."""
    app = create_app(settings=test_settings)
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
