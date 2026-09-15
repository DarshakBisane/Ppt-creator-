"""Health check endpoint."""

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from backend.app import __version__
from backend.app.config import Settings, get_settings

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(default="ok", description="Service health status")
    service: str = Field(..., description="Service name")
    environment: str = Field(..., description="Current deployment environment")
    version: str = Field(default=__version__, description="Service version")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the operational health of the backend service.",
)
async def get_health(request: Request) -> HealthResponse:
    """Return service health status."""
    settings: Settings = getattr(request.app.state, "settings", get_settings())
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        version=__version__,
    )

