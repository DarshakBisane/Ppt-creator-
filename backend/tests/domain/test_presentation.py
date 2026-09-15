"""Tests for Presentation and PresentationMetadata domain models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    CURRENT_SCHEMA_VERSION,
    DesignSystem,
    NarrativeRole,
    Presentation,
    PresentationMetadata,
    Slide,
)


def create_sample_slide(slide_id: str, slide_num: int, title: str = "Sample Slide") -> Slide:
    return Slide(
        id=slide_id,
        slide_number=slide_num,
        title=title,
        narrative_role=NarrativeRole.CONTEXT,
    )


def test_valid_presentation_creation() -> None:
    """Verify clean presentation model instantiates successfully."""
    meta = PresentationMetadata(
        title="Modern Cloud Architecture",
        topic="Cloud Native Transformation",
        slide_count=2,
    )
    slides = [
        create_sample_slide("slide-1", 1, "Executive Overview"),
        create_sample_slide("slide-2", 2, "Architecture Layers"),
    ]
    pres = Presentation(
        schema_version=CURRENT_SCHEMA_VERSION,
        metadata=meta,
        design_system=DesignSystem(),
        slides=slides,
    )

    assert pres.schema_version == "1.0"
    assert len(pres.slides) == 2
    assert pres.slides[0].title == "Executive Overview"
    assert pres.metadata.slide_count == 2


def test_presentation_rejects_empty_slides() -> None:
    """Verify presentation rejects empty slides collection."""
    with pytest.raises(ValidationError) as exc:
        PresentationMetadata(
            title="Empty Presentation",
            topic="No slides",
            slide_count=0,
        )
    assert "greater than or equal to 1" in str(exc.value)

    with pytest.raises(ValidationError) as exc2:
        Presentation(
            metadata=PresentationMetadata(
                title="Empty Presentation",
                topic="No slides",
                slide_count=1,
            ),
            slides=[],
        )
    assert "at least 1 item" in str(exc2.value).lower() or "too_short" in str(exc2.value).lower() or "slide" in str(exc2.value).lower()



def test_presentation_rejects_slide_count_mismatch() -> None:
    """Verify validation fails if metadata slide_count does not equal slides array length."""
    meta = PresentationMetadata(
        title="Mismatch Presentation",
        topic="Count mismatch",
        slide_count=3,
    )
    slides = [
        create_sample_slide("s1", 1),
        create_sample_slide("s2", 2),
    ]
    with pytest.raises(ValidationError) as exc:
        Presentation(
            metadata=meta,
            slides=slides,
        )
    assert "Slide count mismatch" in str(exc.value)


def test_presentation_rejects_duplicate_slide_ids() -> None:
    """Verify duplicate slide IDs raise ValidationError."""
    meta = PresentationMetadata(
        title="Duplicate ID Presentation",
        topic="Duplicate IDs",
        slide_count=2,
    )
    slides = [
        create_sample_slide("duplicate-id", 1),
        create_sample_slide("duplicate-id", 2),
    ]
    with pytest.raises(ValidationError) as exc:
        Presentation(
            metadata=meta,
            slides=slides,
        )
    assert "Duplicate slide id" in str(exc.value)


def test_presentation_rejects_non_sequential_slide_numbers() -> None:
    """Verify non-sequential slide numbers raise ValidationError."""
    meta = PresentationMetadata(
        title="Non-sequential Presentation",
        topic="Sequence gap",
        slide_count=2,
    )
    slides = [
        create_sample_slide("s1", 1),
        create_sample_slide("s2", 5),  # Gap: expected 2
    ]
    with pytest.raises(ValidationError) as exc:
        Presentation(
            metadata=meta,
            slides=slides,
        )
    assert "Must be sequentially 1-indexed" in str(exc.value)


def test_presentation_rejects_invalid_schema_version() -> None:
    """Verify outdated/unsupported schema version is rejected."""
    meta = PresentationMetadata(
        title="Old Version Presentation",
        topic="Version mismatch",
        slide_count=1,
    )
    slides = [create_sample_slide("s1", 1)]
    with pytest.raises(ValidationError) as exc:
        Presentation(
            schema_version="99.0",
            metadata=meta,
            slides=slides,
        )
    assert "Unsupported schema_version" in str(exc.value)
