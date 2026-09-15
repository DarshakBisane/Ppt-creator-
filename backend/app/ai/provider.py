"""AI Provider interface protocol for presentation orchestration."""

from typing import Protocol, runtime_checkable

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.domain.presentation import Presentation


@runtime_checkable
class AIProvider(Protocol):
    """Protocol defining the required interface for presentation generation providers."""

    async def generate_presentation(
        self,
        request: PresentationGenerationRequest,
    ) -> Presentation:
        """Generate a complete, validated Presentation domain model from a user request.

        Args:
            request: Validated PresentationGenerationRequest containing topic, slide count, etc.

        Returns:
            Presentation: Validated presentation domain model conforming to schema.

        Raises:
            AIConfigurationError: Missing or invalid API key or model configuration.
            AIProviderTimeoutError: Provider call exceeded configured timeout.
            AIProviderRateLimitError: Provider rate limit or quota exceeded.
            AIOutputValidationError: Provider returned unrecoverable invalid schema.
            AIProviderError: Unhandled provider or network error.
        """
        ...
