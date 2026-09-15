"""Strongly-typed exceptions for Semantic Visual Selection Intelligence."""

from backend.app.core.errors import AppException


class VisualIntelligenceError(AppException):
    """Base exception for all visual intelligence errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400, code="VISUAL_INTELLIGENCE_ERROR")


class IncompatibleVisualDataError(VisualIntelligenceError):
    """Raised when a visual model cannot be constructed due to missing or invalid data."""

    def __init__(self, visual_type: str, reason: str) -> None:
        super().__init__(
            f"Visual model '{visual_type}' cannot be constructed: {reason}"
        )


class VisualSelectionError(VisualIntelligenceError):
    """Raised when visual selection fails or produces invalid configuration."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Visual selection error: {message}")
