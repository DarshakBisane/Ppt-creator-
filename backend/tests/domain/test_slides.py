"""Tests for Slide and Element domain models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    CardContent,
    Element,
    ElementType,
    NarrativeRole,
    Slide,
    TextContent,
    VisualPlan,
    VisualType,
)


def test_valid_slide_with_elements() -> None:
    """Verify slide with typed elements instantiates cleanly."""
    slide = Slide(
        id="slide-intro-01",
        slide_number=1,
        title="Executive Summary",
        subtitle="Key Strategic Vectors for 2026",
        narrative_role=NarrativeRole.CONTEXT,
        visual_plan=VisualPlan(
            visual_type=VisualType.CARD_GRID,
            intent="Show 3 strategic pillars in cards",
        ),
        elements=[
            Element(
                id="elem-card-1",
                type=ElementType.CARD,
                role="pillar",
                card_content=CardContent(
                    title="Revenue Acceleration",
                    body="Accelerating enterprise ARR by 45% YoY.",
                ),
            ),
            Element(
                id="elem-card-2",
                type=ElementType.CARD,
                role="pillar",
                card_content=CardContent(
                    title="Operational Resilience",
                    body="99.999% SLA availability across cloud regions.",
                ),
            ),
        ],
    )

    assert slide.title == "Executive Summary"
    assert len(slide.elements) == 2
    assert slide.elements[0].card_content is not None
    assert slide.elements[0].card_content.title == "Revenue Acceleration"


def test_slide_rejects_duplicate_element_ids() -> None:
    """Verify duplicate element IDs on the same slide are rejected."""
    with pytest.raises(ValidationError) as exc:
        Slide(
            id="slide-bad-elements",
            slide_number=1,
            title="Bad Slide",
            elements=[
                Element(
                    id="duplicate-elem",
                    type=ElementType.TEXT,
                    text_content=TextContent(text="Block 1"),
                ),
                Element(
                    id="duplicate-elem",
                    type=ElementType.TEXT,
                    text_content=TextContent(text="Block 2"),
                ),
            ],
        )
    assert "Duplicate element id" in str(exc.value)


def test_element_with_nested_children() -> None:
    """Verify hierarchical element grouping works."""
    parent = Element(
        id="group-container",
        type=ElementType.GROUP,
        children=[
            Element(
                id="child-1",
                type=ElementType.TEXT,
                text_content=TextContent(text="Header in group"),
            ),
            Element(
                id="child-2",
                type=ElementType.TEXT,
                text_content=TextContent(text="Body in group"),
            ),
        ],
    )
    assert parent.children is not None
    assert len(parent.children) == 2
