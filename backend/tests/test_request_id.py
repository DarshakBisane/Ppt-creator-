"""Tests for Request ID middleware."""

from fastapi.testclient import TestClient


def test_request_id_generated_when_missing(client: TestClient) -> None:
    """Verify middleware automatically generates a UUID when X-Request-ID is absent."""
    response = client.get("/health")
    assert response.status_code == 200
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    assert len(req_id) >= 32


def test_valid_custom_request_id_preserved(client: TestClient) -> None:
    """Verify safe custom X-Request-ID is preserved and echoed."""
    custom_id = "test-client-req-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_invalid_request_id_replaced_with_safe_uuid(client: TestClient) -> None:
    """Verify unsafe or malformed request IDs are replaced with a safe UUID."""
    malicious_id = "req-id-with-illegal-chars!@#$%^&*()<>?:\"';/~"
    response = client.get("/health", headers={"X-Request-ID": malicious_id})
    assert response.status_code == 200
    returned_id = response.headers.get("X-Request-ID")
    assert returned_id is not None
    assert returned_id != malicious_id


def test_oversized_request_id_replaced(client: TestClient) -> None:
    """Verify oversized request IDs (>64 chars) are rejected and replaced."""
    oversized_id = "a" * 128
    response = client.get("/health", headers={"X-Request-ID": oversized_id})
    assert response.status_code == 200
    returned_id = response.headers.get("X-Request-ID")
    assert returned_id is not None
    assert returned_id != oversized_id
