"""Tests validating request limits and input bounds defenses."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_oversized_topic_rejected():
    """Topic exceeding MAX_PRESENTATION_TOPIC_LENGTH is rejected."""
    long_topic = "A" * 1001
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic=long_topic, slide_count=5)


def test_empty_or_whitespace_topic_rejected():
    """Empty or whitespace only topic is rejected."""
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="   ", slide_count=5)


def test_slides_count_below_minimum_rejected():
    """Slide count less than minimum (3) is rejected."""
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", slide_count=2)

    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", slide_count=0)

    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", slide_count=-5)


def test_slides_count_above_maximum_rejected():
    """Slide count greater than maximum (30) is rejected."""
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", slide_count=31)

    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", slide_count=100)


def test_oversized_audience_field_rejected():
    """Audience exceeding 100 characters is rejected."""
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", audience="A" * 101, slide_count=5)


def test_oversized_purpose_field_rejected():
    """Purpose exceeding 100 characters is rejected."""
    with pytest.raises(ValidationError):
        PresentationGenerationRequest(topic="Valid topic", purpose="P" * 101, slide_count=5)


def test_api_generate_oversized_file_upload_rejected(client):
    """Uploaded reference PPTX larger than allowed size is rejected with 413."""
    # 51 MB payload
    fake_huge_data = b"0" * (51 * 1024 * 1024)
    response = client.post(
        "/api/generate",
        data={"topic": "Testing File Size Limit", "mode": "reference"},
        files={"reference_file": ("huge.pptx", fake_huge_data, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    )
    assert response.status_code == 413
    body = response.json()
    assert body["error"]["code"] == "FILE_TOO_LARGE"
