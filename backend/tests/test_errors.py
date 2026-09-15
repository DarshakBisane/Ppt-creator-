"""Tests for centralized exception handling."""

from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from backend.app.config import Settings
from backend.app.core.errors import BadRequestException, ValidationException
from backend.app.main import create_app

# Router for triggering controlled errors during tests
dummy_router = APIRouter(prefix="/test-errors")


class DummyPayload(BaseModel):
    name: str = Field(..., min_length=3)
    count: int = Field(..., gt=0)


@dummy_router.post("/validation")
async def dummy_validation_endpoint(payload: DummyPayload) -> dict[str, str]:
    return {"message": f"Hello {payload.name}"}


@dummy_router.get("/bad-request")
async def dummy_bad_request_endpoint() -> None:
    raise BadRequestException(message="Custom bad request message")


@dummy_router.get("/domain-validation")
async def dummy_domain_validation_endpoint() -> None:
    raise ValidationException(
        message="Domain validation failed",
        details=[{"field": "slide_count", "issue": "Must be between 1 and 30"}],
    )


@dummy_router.get("/unhandled")
async def dummy_unhandled_endpoint() -> None:
    raise RuntimeError("Unexpected internal crash simulation")


def test_404_structured_error(client: TestClient) -> None:
    """Verify non-existent routes return standardized JSON error structure."""
    response = client.get("/non-existent-route-12345")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "request_id" in data["error"]
    assert data["error"]["request_id"] is not None


def test_validation_structured_error() -> None:
    """Verify request validation errors return 422 with structured field details."""
    app = create_app(Settings(environment="test"))
    app.include_router(dummy_router)
    client = TestClient(app)

    # Missing payload
    response = client.post("/test-errors/validation", json={"name": "a", "count": -5})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) == 2


def test_app_exception_structured_error() -> None:
    """Verify custom AppException returns structured payload."""
    app = create_app(Settings(environment="test"))
    app.include_router(dummy_router)
    client = TestClient(app)

    response = client.get("/test-errors/bad-request")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BAD_REQUEST"
    assert data["error"]["message"] == "Custom bad request message"
    assert data["error"]["request_id"] is not None


def test_domain_validation_exception() -> None:
    """Verify ValidationException returns 422 with custom details."""
    app = create_app(Settings(environment="test"))
    app.include_router(dummy_router)
    client = TestClient(app)

    response = client.get("/test-errors/domain-validation")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"] == [
        {"field": "slide_count", "issue": "Must be between 1 and 30"}
    ]


def test_unhandled_exception_returns_clean_500_without_traceback() -> None:
    """Verify unexpected crashes return a sanitized 500 JSON without traceback."""
    app = create_app(Settings(environment="test"))
    app.include_router(dummy_router)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/test-errors/unhandled")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "traceback" not in str(data).lower()
    assert data["error"]["request_id"] is not None
