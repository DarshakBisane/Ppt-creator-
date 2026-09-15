"""Centralized error handling and standardized JSON error responses."""

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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


def _get_request_id(request: Request) -> str | None:
    """Helper to safely extract request ID from request state."""
    return getattr(request.state, "request_id", None)


from starlette.exceptions import HTTPException as StarletteHTTPException


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
        logger.warning("HTTPException [%d]: %s", exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=code,
                    message=str(exc.detail),
                    request_id=req_id,
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

