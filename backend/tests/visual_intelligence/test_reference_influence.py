"""Tests verifying Reference PPT design context influence and semantic priority."""

from backend.app.ai.context import DesignContext
from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import CardContent, Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Slide
from backend.app.visual_intelligence.selector import SemanticVisualSelector


def test_reference_motif_bonus_boosts_matching_candidate(make_slide) -> None:
    """Design context archetype hints provide a score boost."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Three Key Business Pillars",
        narrative_role=NarrativeRole.CONTEXT,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Pillar A", body="Description")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Pillar B", body="Description")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Pillar C", body="Description")),
        ],
    )
    context = DesignContext(
        design_system=DesignSystem(canvas=CanvasSpec()),
        style_name="dark_tech",
        archetype_hints=["three_card_row", "kpi_dashboard"],
    )

    decision = selector.select_visual_for_slide(slide, design_context=context)
    assert decision.selected_visual_type == VisualType.CARD_GRID
    assert decision.selected_archetype == "three_card_row"


def test_reference_motif_does_not_override_strong_semantic_signal(make_slide) -> None:
    """If reference heavily used cards, but content is clearly a 4-step workflow, Process Flow still wins."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Four-Step User Onboarding Flow: Step 1 -> Step 2 -> Step 3 -> Step 4",
        narrative_role=NarrativeRole.PROCESS,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Step 1: Sign Up", body="User enters email")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Step 2: Verify Phone", body="SMS OTP verification")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Step 3: Setup Profile", body="Upload avatar")),
            Element(id="e4", type=ElementType.CARD, card_content=CardContent(title="Step 4: Go Live", body="Access full dashboard")),
        ],
    )
    # Context preference heavily biases cards
    context = DesignContext(
        design_system=DesignSystem(canvas=CanvasSpec()),
        style_name="clean_editorial",
        archetype_hints=["three_card_row", "four_card_grid"],
    )

    decision = selector.select_visual_for_slide(slide, design_context=context)

    # Process Flow MUST still win because semantic correctness is primary
    assert decision.selected_visual_type == VisualType.PROCESS_FLOW
    assert decision.selected_archetype == "process_flow"
