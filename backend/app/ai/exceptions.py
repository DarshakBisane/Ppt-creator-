"""AI provider and orchestration domain exceptions."""

from typing import Any
from fastapi import status
from backend.app.core.errors import AppException


class AIProviderError(AppException):
    """Base exception for all AI provider and orchestration failures."""

    def __init__(
        self,
        message: str = "An error occurred during AI presentation orchestration.",
        code: str = "AI_PROVIDER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            details=details,
        )
        self.retryable = retryable


class AIConfigurationError(AIProviderError):
    """Raised when AI provider is misconfigured or missing credentials."""

    def __init__(self, message: str = "AI provider is not configured properly. Missing or invalid API credentials.") -> None:
        super().__init__(
            message=message,
            code="AI_CONFIG_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=False,
        )


class AIProviderTimeoutError(AIProviderError):
    """Raised when an AI provider call times out."""

    def __init__(self, message: str = "The AI generation request timed out.") -> None:
        super().__init__(
            message=message,
            code="AI_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            retryable=True,
        )


class AIProviderRateLimitError(AIProviderError):
    """Raised when provider rate limit / quota is exceeded."""

    def __init__(self, message: str = "AI generation capacity exceeded. Please try again shortly.") -> None:
        super().__init__(
            message=message,
            code="AI_RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retryable=True,
        )


class AIOutputValidationError(AIProviderError):
    """Raised when AI structured output fails Pydantic validation after recovery."""

    def __init__(
        self,
        message: str = "AI output could not be validated against the presentation schema.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="AI_OUTPUT_VALIDATION_FAILED",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            retryable=False,
        )
