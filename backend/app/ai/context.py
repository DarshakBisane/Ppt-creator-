"""Context and request models for AI presentation orchestration."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator

from backend.app.domain.constants import (
    MAX_PRESENTATION_TOPIC_LENGTH,
)
from backend.app.domain.design_system import DesignSystem


class DesignContext(BaseModel):
    """Sanitized design tokens extracted from reference deck or pre-configured style."""

    design_system: DesignSystem = Field(default_factory=DesignSystem)
    style_name: str = Field(default="custom", max_length=50)
    archetype_hints: list[str] = Field(default_factory=list, max_length=10)


class PresentationGenerationRequest(BaseModel):
    """Validated input request for AI presentation generation."""

    mode: Literal["topic", "reference"] = Field(
        default="topic",
        description="Generation mode: 'topic' creates fresh structure; 'reference' transfers design language.",
    )
    topic: str = Field(
        ...,
        min_length=3,
        max_length=MAX_PRESENTATION_TOPIC_LENGTH,
        description="Presentation topic or detailed prompt.",
    )
    audience: str | None = Field(
        default=None,
        max_length=100,
        description="Target audience (e.g. Executives, Engineers, Students).",
    )
    purpose: str | None = Field(
        default=None,
        max_length=100,
        description="Presentation goal (e.g. Business Pitch, Technical Deep-Dive).",
    )
    slide_count: int = Field(
        default=8,
        ge=3,
        le=30,
        description="Target number of slides (between 3 and 30).",
    )
    style: str = Field(
        default="professional",
        max_length=50,
        description="Visual style aesthetic (e.g. professional, modern_dark, minimal, corporate, creative).",
    )
    design_context: DesignContext | None = Field(
        default=None,
        description="Sanitized design tokens if generated in reference mode.",
    )

    @field_validator("topic")
    @classmethod
    def sanitize_topic_text(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Presentation topic cannot be empty or whitespace only.")
        return clean
