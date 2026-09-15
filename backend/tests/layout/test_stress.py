"""Stress and edge-case tests for the deterministic layout engine."""

import pytest

from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.layout.engine import LayoutEngine


def test_minimal_single_slide_layout() -> None:
    """Verify layout on minimal slide with zero optional fields."""
    slide = Slide(
        id="s_min",
        slide_number=1,
        title="Minimal",
        narrative_role=NarrativeRole.TITLE,
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Min", topic="Min", slide_count=1),
        slides=[slide],
    )

    engine = LayoutEngine()
    result = engine.layout_presentation(pres)
    assert len(result.slides) == 1
    assert len(result.slides[0].elements) >= 1


def test_large_deck_layout_stress() -> None:
    """Verify layout performance across a large presentation deck (50 slides)."""
    slides = [
        Slide(
            id=f"slide_{i}",
            slide_number=i,
            title=f"Stress Slide #{i}",
            subtitle=f"Performance evaluation at index {i}",
            narrative_role=NarrativeRole.CONTEXT if i % 2 == 0 else NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID if i % 2 == 0 else VisualType.KPI),
        )
        for i in range(1, 51)
    ]
    pres = Presentation(
        metadata=PresentationMetadata(title="Stress Deck", topic="Stress Testing", slide_count=50),
        slides=slides,
    )

    engine = LayoutEngine()
    result = engine.layout_presentation(pres)
    assert len(result.slides) == 50


def test_extreme_content_lengths_and_many_cards() -> None:
    """Verify handling of slides with many cards and very long titles."""
    long_title = "Strategic Scalability Transformation of Enterprise Systems Across Cloud and Hybrid Environments"
    elements = [
        Element(
            id=f"card_{i}",
            type=ElementType.CARD,
            card_content=CardContent(
                title=f"Module #{i} Performance",
                body="Detailed operational metrics " * 10,
            ),
        )
        for i in range(8)
    ]

    slide = Slide(
        id="s_extreme",
        slide_number=2,
        title=long_title,
        subtitle="Evaluating robustness under high density",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=elements,
    )

    engine = LayoutEngine()
    res = engine.layout_slide(slide)
    assert res.slide_id == "s_extreme"
    assert len(res.elements) > 0
    # Every element must have valid non-negative dimensions
    for e in res.elements:
        assert e.rect.width > 0
        assert e.rect.height > 0
