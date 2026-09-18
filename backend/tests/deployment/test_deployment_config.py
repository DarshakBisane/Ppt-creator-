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


def test_production_wildcard_cors_prohibited() -> None:
    """Wildcard '*' CORS origins raise ValueError in production mode."""
    with pytest.raises(ValueError, match="Wildcard.*CORS"):
        Settings(environment="production", cors_origins="*")

    with pytest.raises(ValueError, match="Wildcard.*CORS"):
        Settings(environment="production", cors_origins=["*"])


def test_non_positive_resource_limits_rejected() -> None:
    """Non-positive values for concurrent jobs, TTL, or timeout raise ValueError."""
    with pytest.raises(ValueError, match="max_concurrent_jobs"):
        Settings(max_concurrent_jobs=0)

    with pytest.raises(ValueError, match="max_job_runtime_seconds"):
        Settings(max_job_runtime_seconds=0)

    with pytest.raises(ValueError, match="artifact_ttl_seconds"):
        Settings(artifact_ttl_seconds=0)


def test_sanitize_filename_encoded_traversals_and_executables() -> None:
    """sanitize_filename prevents URL-encoded directory traversal, null bytes, and executable extensions."""
    from backend.app.artifacts.storage import sanitize_filename

    # URL-encoded traversal
    assert sanitize_filename("%2e%2e%2f%2e%2e%2fetc%2fpasswd") == "passwd.pptx"
    assert sanitize_filename("%2e%2e%5cwindows%5cboot.ini") == "boot.ini.pptx"
    
    # Null bytes
    assert sanitize_filename("safe_report\x00.exe") == "safe_report.pptx"
    
    # Executable / script extension stripping
    assert sanitize_filename("malicious_script.sh") == "malicious_script.pptx"
    assert sanitize_filename("trojan.exe") == "trojan.pptx"
    assert sanitize_filename("payload.py") == "payload.pptx"
    
    # Legitimate filename preserved
    assert sanitize_filename("Quantum_Computing_2026.pptx") == "Quantum_Computing_2026.pptx"


def test_queued_job_cannot_jump_to_completed() -> None:
    """A job in QUEUED status cannot jump directly to COMPLETED."""
    from backend.app.jobs.store import MemoryJobStore
    from backend.app.ai.context import PresentationGenerationRequest
    from backend.app.core.errors import JobStateError

    store = MemoryJobStore()
    req = PresentationGenerationRequest(topic="Illegal Transition Test", slide_count=4)
    store.create_job("job-illegal-jump-1", req)

    with pytest.raises(JobStateError, match="Invalid state transition"):
        store.complete_job("job-illegal-jump-1", artifact_path="/tmp/art.pptx", filename="Pres.pptx", slide_count=4)

