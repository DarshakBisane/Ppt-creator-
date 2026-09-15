"""Domain exceptions for Visual Quality Assurance and Auto-Correction."""

from backend.app.core.errors import AppException


class VisualQAException(AppException):
    """Base exception for all Visual QA and auto-correction failures."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VISUAL_QA_ERROR",
            details=details,
        )


class UnrecoverableLayoutError(VisualQAException):
    """Raised when a slide layout cannot be made valid after all 3 correction passes."""

    def __init__(self, slide_id: str, message: str, details: dict | None = None) -> None:
        merged_details = {"slide_id": slide_id}
        if details:
            merged_details.update(details)
        super().__init__(
            message=f"Slide '{slide_id}' has unrecoverable layout issues: {message}",
            details=merged_details,
        )


class InvalidGeometryError(VisualQAException):
    """Raised when element geometry contains non-positive or corrupted dimensions."""

    def __init__(self, element_id: str, message: str) -> None:
        super().__init__(
            message=f"Element '{element_id}' geometry is invalid: {message}",
            details={"element_id": element_id},
        )
