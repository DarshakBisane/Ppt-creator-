"""Tests for /health endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient) -> None:
    """Verify health endpoint returns 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Test Presentation Generator"
    assert data["environment"] == "test"
    assert "version" in data


def test_health_endpoint_includes_request_id_header(client: TestClient) -> None:
    """Verify health endpoint returns X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0
