"""Centralized error handling and standardized JSON error responses."""

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Structured error payload."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    request_id: str | None = Field(default=None, description="Request correlation ID")
    details: list[dict[str, Any]] | None = Field(default=None, description="Optional detailed error context")


class ErrorResponse(BaseModel):
    """Standardized top-level API error response."""

    error: ErrorDetail


class AppException(Exception):
    """Base application exception for business and domain errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An unexpected error occurred.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

    @property
    def error_code(self) -> str:
        """Alias for code property for backwards/forwards compatibility."""
        return self.code


class BadRequestException(AppException):
    """400 Bad Request."""

    def __init__(self, message: str = "Invalid request parameters.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="BAD_REQUEST",
            message=message,
            details=details,
        )


class NotFoundException(AppException):
    """404 Not Found."""

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message,
        )


class ValidationException(AppException):
    """422 Unprocessable Entity for domain validation failures."""

    def __init__(self, message: str = "Validation failed.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class ConflictException(AppException):
    """409 Conflict."""

    def __init__(self, message: str = "A conflict occurred with existing resource state.") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=message,
        )


class InternalServerException(AppException):
    """500 Internal Server Error."""

    def __init__(self, message: str = "An unexpected server error occurred.") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message=message,
        )


# =====================================================================
# Domain Pipeline Exceptions
# =====================================================================

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


class SemanticSelectionError(AppException):
    """Raised when semantic archetype selection fails."""

    def __init__(self, message: str = "Failed to select appropriate visual archetypes.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SEMANTIC_SELECTION_ERROR",
            message=message,
            details=details,
        )


class LayoutError(AppException):
    """Raised when 1920x1080 layout geometry computation fails."""

    def __init__(self, message: str = "Failed to compute layout coordinates.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="LAYOUT_ERROR",
            message=message,
            details=details,
        )


class VisualQAError(AppException):
    """Raised when visual quality assurance validation or repair fails."""

    def __init__(self, message: str = "Visual quality inspection and repair failed.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="VISUAL_QA_ERROR",
            message=message,
            details=details,
        )


class RenderingError(AppException):
    """Raised when OpenXML PPTX rendering fails."""

    def __init__(self, message: str = "Failed to render PowerPoint OpenXML document.", details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="RENDERING_ERROR",
            message=message,
            details=details,
        )


class ArtifactStorageError(AppException, ValueError):
    """Base exception for artifact persistence failures."""

    def __init__(
        self,
        message: str = "Artifact storage operation failed.",
        code: str = "ARTIFACT_STORAGE_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, code=code, message=message, details=details)


class ArtifactSecurityError(ArtifactStorageError):
    """Raised when an unsafe artifact path or traversal attempt is detected."""

    def __init__(self, message: str = "Unsafe path or storage access violation detected.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ARTIFACT_SECURITY_VIOLATION",
            message=message,
        )


class ArtifactNotFoundError(ArtifactStorageError):
    """Raised when an artifact file does not exist on disk."""

    def __init__(self, message: str = "Artifact file was not found or has expired.") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ARTIFACT_NOT_FOUND",
            message=message,
        )


class ArtifactValidationError(ArtifactStorageError):
    """Raised when generated PPTX fails package integrity validation."""

    def __init__(self, message: str = "Generated PowerPoint package failed integrity validation.") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PPTX_VALIDATION_ERROR",
            message=message,
        )


class JobError(AppException):
    """Base exception for job lifecycle operations."""

    def __init__(
        self,
        message: str = "Job management error.",
        code: str = "JOB_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, code=code, message=message, details=details)


class JobNotFoundError(JobError):
    """Raised when a job ID is not found in the store."""

    def __init__(self, message: str = "Presentation generation job was not found.") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="JOB_NOT_FOUND",
            message=message,
        )


class JobStateError(JobError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, message: str = "Invalid job state transition attempted.") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_JOB_STATE_TRANSITION",
            message=message,
        )


class JobTimeoutError(JobError):
    """Raised when a job exceeds maximum execution runtime."""

    def __init__(self, message: str = "Presentation generation exceeded maximum runtime limit. Please try again.") -> None:
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="JOB_TIMEOUT",
            message=message,
        )


class JobConcurrencyError(JobError):
    """Raised when generation capacity is temporarily exhausted."""

    def __init__(self, message: str = "Too many presentations are being generated right now. Please try again shortly.") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="JOB_CAPACITY_EXCEEDED",
            message=message,
        )


class ConfigurationError(AppException):
    """Raised when service configuration or credentials are missing or invalid."""

    def __init__(self, message: str = "Service configuration error.") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="CONFIGURATION_ERROR",
            message=message,
        )


def _get_request_id(request: Request) -> str | None:
    """Helper to safely extract request ID from request state."""
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all standard exception handlers on the FastAPI app instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = _get_request_id(request)
        logger.warning(
            "AppException [%s]: %s (status=%d)",
            exc.code,
            exc.message,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    request_id=req_id,
                    details=exc.details,
                )
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = _get_request_id(request)
        formatted_details = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        logger.warning("Request validation failed: %s", formatted_details)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="The request body or parameters failed validation.",
                    request_id=req_id,
                    details=formatted_details,
                )
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException | HTTPException) -> JSONResponse:
        req_id = _get_request_id(request)
        code = f"HTTP_{exc.status_code}"
        message = str(exc.detail)
        details = None

        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", code)
            message = exc.detail.get("message", str(exc.detail))
            details = exc.detail.get("details", None)

        logger.warning("HTTPException [%d]: %s", exc.status_code, message)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=code,
                    message=message,
                    request_id=req_id,
                    details=details,
                )
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = _get_request_id(request)
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected internal server error occurred.",
                    request_id=req_id,
                )
            ).model_dump(),
        )
