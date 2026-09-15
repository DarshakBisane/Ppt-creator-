"""Unit tests for 1-pass recovery handler and response schema validation."""

import json
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.recovery import OnePassRecoveryHandler
from backend.app.domain.presentation import Presentation


def test_parse_and_validate_valid_json():
    req = PresentationGenerationRequest(topic="Testing Recovery Pipeline", slide_count=4)
    expected_pres = FakeAIProvider.create_deterministic_presentation(req)
    raw_json = expected_pres.model_dump_json()

    pres, error = OnePassRecoveryHandler.parse_and_validate(raw_json)
    assert error is None
    assert pres is not None
    assert isinstance(pres, Presentation)
    assert pres.metadata.slide_count == 4
    assert len(pres.slides) == 4


def test_parse_and_validate_markdown_fenced_json():
    req = PresentationGenerationRequest(topic="Testing Markdown Stripping", slide_count=3)
    expected_pres = FakeAIProvider.create_deterministic_presentation(req)
    raw_json = f"```json\n{expected_pres.model_dump_json()}\n```"

    pres, error = OnePassRecoveryHandler.parse_and_validate(raw_json)
    assert error is None
    assert pres is not None
    assert pres.metadata.slide_count == 3


def test_parse_and_validate_dict():
    req = PresentationGenerationRequest(topic="Testing Dict Validation", slide_count=3)
    expected_pres = FakeAIProvider.create_deterministic_presentation(req)
    raw_dict = expected_pres.model_dump()

    pres, error = OnePassRecoveryHandler.parse_and_validate(raw_dict)
    assert error is None
    assert pres is not None
    assert pres.metadata.title == expected_pres.metadata.title


def test_parse_and_validate_malformed_json():
    malformed = '{"metadata": {"title": "broken"'
    pres, error = OnePassRecoveryHandler.parse_and_validate(malformed)
    assert pres is None
    assert error is not None
    assert "Invalid JSON" in error or "Malformed JSON" in error


def test_parse_and_validate_schema_mismatch():
    invalid_schema = json.dumps({
        "schema_version": "1.0.0",
        "metadata": {
            "title": "Missing fields",
            "topic": "Testing",
            "slide_count": 2,
        },
        "slides": [],
    })
    pres, error = OnePassRecoveryHandler.parse_and_validate(invalid_schema)
    assert pres is None
    assert error is not None
    assert "Location" in error


def test_parse_and_validate_invalid_input_type():
    pres, error = OnePassRecoveryHandler.parse_and_validate(12345)  # type: ignore
    assert pres is None
    assert "Unexpected response type: int" in error
