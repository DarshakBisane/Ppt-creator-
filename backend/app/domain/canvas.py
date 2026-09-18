"""Canvas specification models."""

from typing import Literal
from pydantic import BaseModel, Field

from backend.app.domain.constants import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_CANVAS_WIDTH,
)


class CanvasSpec(BaseModel):
    """Virtual presentation canvas specifications (internal 16:9 coordinate space)."""

    width: int = Field(
        default=DEFAULT_CANVAS_WIDTH,
        description="Virtual canvas width in points (standard 1920)",
        ge=1,
    )
    height: int = Field(
        default=DEFAULT_CANVAS_HEIGHT,
        description="Virtual canvas height in points (standard 1080)",
        ge=1,
    )
    aspect_ratio: str = Field(
        default=DEFAULT_ASPECT_RATIO,
        description="Target aspect ratio",
    )
    orientation: Literal["landscape", "portrait"] = Field(
        default="landscape",
        description="Slide orientation",
    )
