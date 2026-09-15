"""Unit tests for the 3-Pass Auto-Correction engine and monotonic quality score guarantees."""

from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.layout.engine import LayoutEngine
from backend.app.layout.models import ElementGeometry, Rect, SlideLayoutResult
from backend.app.layout.spacing import generate_ports
from backend.app.visual_qa.correction_pass import ThreePassCorrectionEngine


def test_pass_1_local_correction_success() -> None:
    """An element slightly out-of-bounds (e.g. x=-20) is repaired in Pass 1 without re-layout."""
    engine = ThreePassCorrectionEngine()
    slide = Slide(
        id="s1_local",
        slide_number=1,
        title="Local Fix Slide",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="Card 1", body="Body content")),
        ],
    )

    # Broken initial layout with negative X
    broken_card = ElementGeometry(
        id="c1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=-20, y=200, width=500, height=300),
        ports=generate_ports("c1", Rect(x=-20, y=200, width=500, height=300)),
        content_data=CardContent(title="Card 1", body="Body content"),
    )
    initial_layout = SlideLayoutResult(
        slide_id="s1_local",
        slide_number=1,
        visual_type=VisualType.CARD_GRID,
        narrative_role=NarrativeRole.SOLUTION,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
        elements=[broken_card],
    )

    result = engine.correct_slide(slide, initial_layout)
    assert result.passes_executed >= 1
    # Card X should now be clamped inside safe area >= 0
    fixed_elem = next(e for e in result.layout.elements if e.id == "c1")
    assert fixed_elem.rect.x >= 0
    assert result.passed is True


def test_pass_3_safe_fallback_when_archetype_empty() -> None:
    """A Timeline slide with no milestone data falls back in Pass 3 to a compatible fallback archetype."""
    engine = ThreePassCorrectionEngine()
    slide = Slide(
        id="s_timeline",
        slide_number=2,
        title="Future Milestones",
        narrative_role=NarrativeRole.TIMELINE,
        visual_plan=VisualPlan(visual_type=VisualType.TIMELINE),
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Phase 1", body="Initial release")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Phase 2", body="Scale deployment")),
        ],
    )

    layout_engine = LayoutEngine()
    initial_layout = layout_engine.layout_slide(slide)

    result = engine.correct_slide(slide, initial_layout)
    assert result.passes_executed <= 3
    assert result.quality_score >= 70.0


def test_monotonicity_guarantee_never_degrades_score() -> None:
    """A slide result after auto-correction never produces a worse quality score than initial."""
    engine = ThreePassCorrectionEngine()
    slide = Slide(
        id="s_mono",
        slide_number=3,
        title="Monotonic Test",
        narrative_role=NarrativeRole.CONTEXT,
        visual_plan=VisualPlan(visual_type=VisualType.TEXT),
        elements=[
            Element(id="e1", type=ElementType.TEXT, text_content=TextContent(text="Regular text paragraph")),
        ],
    )

    layout_engine = LayoutEngine()
    initial_layout = layout_engine.layout_slide(slide)
    initial_qa = engine.analyzer.analyze(initial_layout, slide)

    result = engine.correct_slide(slide, initial_layout)
    assert result.quality_score >= initial_qa.quality_score
