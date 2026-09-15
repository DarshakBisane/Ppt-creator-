"""AI Orchestration package for AI Presentation Generator."""

from backend.app.ai.context import DesignContext, PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIConfigurationError,
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.ai.gemini_provider import GeminiProvider
from backend.app.ai.prompts import PromptBuilder
from backend.app.ai.provider import AIProvider
from backend.app.ai.recovery import OnePassRecoveryHandler

__all__ = [
    "AIConfigurationError",
    "AIOutputValidationError",
    "AIProvider",
    "AIProviderError",
    "AIProviderRateLimitError",
    "AIProviderTimeoutError",
    "DesignContext",
    "FakeAIProvider",
    "GeminiProvider",
    "OnePassRecoveryHandler",
    "PresentationGenerationRequest",
    "PromptBuilder",
]
