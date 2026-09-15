"""Canonical Presentation and Slide domain models."""

from pydantic import BaseModel, Field, model_validator

from backend.app.domain.constants import (
    CURRENT_SCHEMA_VERSION,
    MAX_ELEMENTS_PER_SLIDE,
    MAX_PRESENTATION_TITLE_LENGTH,
    MAX_PRESENTATION_TOPIC_LENGTH,
    MAX_SLIDE_SUBTITLE_LENGTH,
    MAX_SLIDE_TITLE_LENGTH,
    MAX_SLIDES_COUNT,
    MAX_SPEAKER_NOTES_LENGTH,
    MIN_SLIDES_COUNT,
)
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import NarrativeRole
from backend.app.domain.visuals import VisualPlan


class Slide(BaseModel):
    """Semantic slide content specification."""

    id: str = Field(..., min_length=1, max_length=64, description="Unique slide identifier")
    slide_number: int = Field(..., ge=1, description="1-indexed slide sequence number")
    title: str = Field(..., min_length=1, max_length=MAX_SLIDE_TITLE_LENGTH)
    subtitle: str | None = Field(default=None, max_length=MAX_SLIDE_SUBTITLE_LENGTH)
    narrative_role: NarrativeRole = Field(
        default=NarrativeRole.CONTEXT,
        description="Slide purpose in the presentation narrative flow",
    )
    purpose: str | None = Field(default=None, max_length=300)
    visual_plan: VisualPlan = Field(
        default_factory=VisualPlan,
        description="Semantic visual plan for deterministic layout selection",
    )
    elements: list[Element] = Field(
        default_factory=list,
        max_length=MAX_ELEMENTS_PER_SLIDE,
        description="Structured semantic content elements",
    )
    speaker_notes: str | None = Field(
        default=None,
        max_length=MAX_SPEAKER_NOTES_LENGTH,
        description="Optional presenter notes",
    )

    @model_validator(mode="after")
    def validate_unique_element_ids(self) -> "Slide":
        seen_ids: set[str] = set()
        for elem in self.elements:
            if elem.id in seen_ids:
                raise ValueError(f"Duplicate element id '{elem.id}' detected in slide #{self.slide_number}")
            seen_ids.add(elem.id)
        return self


class PresentationMetadata(BaseModel):
    """Presentation high-level metadata."""

    title: str = Field(..., min_length=1, max_length=MAX_PRESENTATION_TITLE_LENGTH)
    topic: str = Field(..., min_length=1, max_length=MAX_PRESENTATION_TOPIC_LENGTH)
    subtitle: str | None = Field(default=None, max_length=MAX_SLIDE_SUBTITLE_LENGTH)
    audience: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, max_length=100)
    language: str = Field(default="en", max_length=10)
    slide_count: int = Field(..., ge=MIN_SLIDES_COUNT, le=MAX_SLIDES_COUNT)


class Presentation(BaseModel):
    """Canonical root Presentation domain model."""

    schema_version: str = Field(
        default=CURRENT_SCHEMA_VERSION,
        description="Presentation schema version for forwards/backwards compatibility",
    )
    metadata: PresentationMetadata
    design_system: DesignSystem = Field(default_factory=DesignSystem)
    slides: list[Slide] = Field(..., min_length=MIN_SLIDES_COUNT, max_length=MAX_SLIDES_COUNT)
    generation_metadata: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_presentation_integrity(self) -> "Presentation":
        # 1. Verify schema version
        if self.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema_version '{self.schema_version}'. Expected '{CURRENT_SCHEMA_VERSION}'."
            )

        # 2. Verify slide count matches metadata
        actual_count = len(self.slides)
        if actual_count != self.metadata.slide_count:
            raise ValueError(
                f"Slide count mismatch: metadata specifies {self.metadata.slide_count} slides, but presentation contains {actual_count} slides."
            )

        # 3. Verify unique slide IDs and sequential numbers
        seen_slide_ids: set[str] = set()
        for idx, slide in enumerate(self.slides, start=1):
            if slide.id in seen_slide_ids:
                raise ValueError(f"Duplicate slide id '{slide.id}' detected at slide #{idx}")
            seen_slide_ids.add(slide.id)

            if slide.slide_number != idx:
                raise ValueError(
                    f"Slide #{idx} has invalid slide_number {slide.slide_number}. Must be sequentially 1-indexed."
                )

        return self
