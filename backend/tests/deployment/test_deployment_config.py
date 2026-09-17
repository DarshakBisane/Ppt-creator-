"""Deployment, configuration, containerization, and production hardening tests."""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app import __version__


def test_production_environment_settings() -> None:
    """Production mode defaults docs to disabled and sets production flag."""
    settings = Settings(
        environment="production",
        gemini_api_key="test_key",
    )
    assert settings.is_production is True
    assert settings.is_development is False
    assert settings.show_docs is False


def test_development_environment_settings() -> None:
    """Development mode enables docs by default."""
    settings = Settings(
        environment="development",
    )
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.show_docs is True


def test_enable_docs_explicit_override() -> None:
    """Explicit enable_docs flag overrides environment default."""
    prod_with_docs = Settings(environment="production", enable_docs=True)
    assert prod_with_docs.show_docs is True

    dev_without_docs = Settings(environment="development", enable_docs=False)
    assert dev_without_docs.show_docs is False


def test_cors_origins_parsing() -> None:
    """CORS origins parse correctly from comma-separated string or list."""
    # From comma-separated string
    settings_str = Settings(cors_origins="https://presenai.app, https://app.presenai.com, http://localhost:3000")  # type: ignore
    assert settings_str.cors_origins == [
        "https://presenai.app",
        "https://app.presenai.com",
        "http://localhost:3000",
    ]

    # From list
    settings_list = Settings(cors_origins=["http://localhost:5173", "http://127.0.0.1:5173"])
    assert settings_list.cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_health_endpoint_response_structure_and_speed() -> None:
    """GET /health returns valid payload deterministically with low latency."""
    settings = Settings(
        app_name="PresenAI Test",
        environment="production",
    )
    app = create_app(settings=settings)
    client = TestClient(app)

    start = time.perf_counter()
    response = client.get("/health")
    duration_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "PresenAI Test"
    assert data["environment"] == "production"
    assert data["version"] == __version__
    # Health check must be fast and deterministic (< 100ms in local testing)
    assert duration_ms < 100


def test_production_docs_disabled_by_default() -> None:
    """Swagger and ReDoc endpoints return 404 in production when enable_docs=False."""
    prod_settings = Settings(
        environment="production",
        enable_docs=False,
    )
    app = create_app(settings=prod_settings)
    client = TestClient(app)

    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 404

    redoc_resp = client.get("/redoc")
    assert redoc_resp.status_code == 404

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 404


def test_development_docs_enabled_by_default() -> None:
    """Swagger endpoints are accessible in development mode."""
    dev_settings = Settings(
        environment="development",
    )
    app = create_app(settings=dev_settings)
    client = TestClient(app)

    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200


def test_request_id_header_injected_in_responses() -> None:
    """Every HTTP response receives an X-Request-ID tracking header."""
    app = create_app(settings=Settings(environment="production"))
    client = TestClient(app)

    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0


def test_unhandled_error_sanitization_in_production() -> None:
    """Internal exceptions return safe structured JSON without raw tracebacks."""
    app = create_app(settings=Settings(environment="production"))
    
    # Inject a route that raises an unexpected RuntimeError
    @app.get("/test-internal-error")
    def trigger_error():
        raise RuntimeError("Secret DB connection string: postgres://admin:password@db:5432/main")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test-internal-error")

    assert resp.status_code == 500
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Verify no raw exception text / secret leaked
    assert "postgres://" not in resp.text
    assert "password" not in resp.text
    assert "Traceback" not in resp.text
