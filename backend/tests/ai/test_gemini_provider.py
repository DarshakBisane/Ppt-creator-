"""Unit tests for GeminiProvider with mocked google-genai SDK."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from google.genai.errors import APIError

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIConfigurationError,
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.ai.gemini_provider import GeminiProvider
from backend.app.domain.presentation import Presentation


def create_mock_gemini_client(return_texts: list[str]) -> MagicMock:
    """Create a mock google-genai Client returning specified text responses."""
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    side_effects = []
    for text in return_texts:
        mock_resp = MagicMock()
        mock_resp.text = text
        side_effects.append(mock_resp)

    mock_models.generate_content = AsyncMock(side_effect=side_effects)
    mock_aio.models = mock_models
    mock_client.aio = mock_aio
    return mock_client


@pytest.mark.asyncio
async def test_gemini_provider_missing_api_key_raises_config_error():
    provider = GeminiProvider(api_key="", client=None)
    req = PresentationGenerationRequest(topic="Missing API Key")

    with pytest.raises(AIConfigurationError) as exc_info:
        await provider.generate_presentation(req)

    assert "Gemini API key is not configured" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_gemini_provider_valid_first_attempt():
    req = PresentationGenerationRequest(topic="Autonomous Systems in 2026", slide_count=4)
    valid_pres = FakeAIProvider.create_deterministic_presentation(req)
    valid_json = valid_pres.model_dump_json()

    mock_client = create_mock_gemini_client([valid_json])
    provider = GeminiProvider(api_key="test-key", client=mock_client)

    result = await provider.generate_presentation(req)

    assert isinstance(result, Presentation)
    assert result.metadata.slide_count == 4
    assert mock_client.aio.models.generate_content.call_count == 1


@pytest.mark.asyncio
async def test_gemini_provider_one_pass_recovery_success():
    req = PresentationGenerationRequest(topic="Autonomous Systems in 2026", slide_count=4)
    valid_pres = FakeAIProvider.create_deterministic_presentation(req)
    valid_json = valid_pres.model_dump_json()

    # First attempt returns invalid JSON, second attempt returns valid JSON
    mock_client = create_mock_gemini_client([
        '{"invalid": "incomplete json',
        valid_json,
    ])
    provider = GeminiProvider(api_key="test-key", client=mock_client)

    result = await provider.generate_presentation(req)

    assert isinstance(result, Presentation)
    assert result.metadata.slide_count == 4
    # Verified exactly 2 attempts
    assert mock_client.aio.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_fails_after_two_attempts():
    req = PresentationGenerationRequest(topic="Autonomous Systems in 2026", slide_count=4)

    # Both attempts return invalid schema
    mock_client = create_mock_gemini_client([
        '{"bad": "schema_attempt_1"}',
        '{"bad": "schema_attempt_2"}',
    ])
    provider = GeminiProvider(api_key="test-key", client=mock_client)

    with pytest.raises(AIOutputValidationError) as exc_info:
        await provider.generate_presentation(req)

    assert "AI output validation failed after 2 attempts" in str(exc_info.value.message)
    # Never exceeds 2 attempts
    assert mock_client.aio.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_handles_timeout():
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    async def timeout_side_effect(*args, **kwargs):
        raise asyncio.TimeoutError("Timeout occurred")

    mock_models.generate_content = AsyncMock(side_effect=timeout_side_effect)
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    provider = GeminiProvider(api_key="test-key", timeout_seconds=0.1, client=mock_client)
    req = PresentationGenerationRequest(topic="Timeout Test")

    with pytest.raises(AIProviderTimeoutError):
        await provider.generate_presentation(req)


@pytest.mark.asyncio
async def test_gemini_provider_handles_rate_limit():
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    # Create mock APIError with 429 code
    api_err = APIError(429, {"error": {"message": "Resource exhausted: quota exceeded"}})

    mock_models.generate_content = AsyncMock(side_effect=api_err)
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = PresentationGenerationRequest(topic="Rate Limit Test")

    with pytest.raises(AIProviderRateLimitError):
        await provider.generate_presentation(req)


@pytest.mark.asyncio
async def test_gemini_provider_handles_empty_response():
    mock_client = create_mock_gemini_client(["   "])
    provider = GeminiProvider(api_key="test-key", client=mock_client)
    req = PresentationGenerationRequest(topic="Empty Response Test")

    with pytest.raises(AIProviderError) as exc_info:
        await provider.generate_presentation(req)

    assert "empty response" in str(exc_info.value.message).lower()
