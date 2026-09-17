"""Tests verifying AI error mapping, timeout handling, and 1-pass recovery bounds."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from google.genai.errors import APIError

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIConfigurationError,
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_missing_api_key_raises_config_error():
    """GeminiProvider raises AIConfigurationError when API key is missing or empty."""
    provider = GeminiProvider(api_key="")
    with pytest.raises(AIConfigurationError) as exc_info:
        _ = provider.client
    assert "GEMINI_API_KEY" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gemini_call_timeout_raises_provider_timeout_error():
    """GeminiProvider raises AIProviderTimeoutError on network call timeout."""
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    async def hanging_call(*args, **kwargs):
        await asyncio.sleep(5)

    mock_models.generate_content = hanging_call
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    provider = GeminiProvider(
        api_key="test-key",
        timeout_seconds=0.1,
        client=mock_client,
    )

    with pytest.raises(AIProviderTimeoutError) as exc_info:
        await provider._execute_model_call("sys instruction", "prompt")
    assert exc_info.value.code == "AI_TIMEOUT"
    assert "timed out" in exc_info.value.message


@pytest.mark.asyncio
async def test_gemini_rate_limit_error_mapping():
    """Gemini APIError 429 maps to AIProviderRateLimitError."""
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    mock_api_error = APIError(429, "Resource exhausted: quota exceeded")
    mock_models.generate_content = AsyncMock(side_effect=mock_api_error)
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    provider = GeminiProvider(
        api_key="test-key",
        timeout_seconds=5.0,
        client=mock_client,
    )

    with pytest.raises(AIProviderRateLimitError) as exc_info:
        await provider._execute_model_call("sys instruction", "prompt")
    assert exc_info.value.code == "AI_RATE_LIMITED"


@pytest.mark.asyncio
async def test_gemini_strictly_bounds_to_two_attempts():
    """GeminiProvider exhausts after exactly 2 attempts on invalid structured output."""
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()

    # Returns invalid JSON both times
    mock_resp = MagicMock()
    mock_resp.text = '{"invalid": "schema"}'
    mock_models.generate_content = AsyncMock(return_value=mock_resp)
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    provider = GeminiProvider(
        api_key="test-key",
        max_attempts=2,
        client=mock_client,
    )

    request = PresentationGenerationRequest(topic="Testing Schema Recovery Bounds", slide_count=4)
    with pytest.raises(AIOutputValidationError) as exc_info:
        await provider.generate_presentation(request)

    assert exc_info.value.code == "AI_OUTPUT_VALIDATION_FAILED"
    # Verify exactly 2 calls made
    assert mock_models.generate_content.call_count == 2
