"""Tests for deck visual budget enforcement and repetition penalties."""

from backend.app.domain.elements import CardContent, Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.visual_intelligence.models import DeckVisualBudget
from backend.app.visual_intelligence.selector import SemanticVisualSelector


def test_deck_visual_budget_penalizes_consecutive_same_archetypes() -> None:
    budget = DeckVisualBudget(max_consecutive_same_archetype=2)

    # Record two consecutive card grids
    budget.record_selection(VisualType.CARD_GRID, "three_card_row")
    budget.record_selection(VisualType.CARD_GRID, "three_card_row")

    penalty = budget.get_repetition_penalty("three_card_row")
    assert penalty >= 0.60


def test_deck_refinement_maintains_visual_diversity(make_slide) -> None:
    selector = SemanticVisualSelector()

    # Create a 4-slide presentation with generic cards
    slides = [
        make_slide(title=f"Core Pillar {i+1}", narrative_role=NarrativeRole.CONTEXT, elements=[
            Element(id=f"e{i}_1", type=ElementType.CARD, card_content=CardContent(title=f"Item {i}-1", body="Desc")),
            Element(id=f"e{i}_2", type=ElementType.CARD, card_content=CardContent(title=f"Item {i}-2", body="Desc")),
            Element(id=f"e{i}_3", type=ElementType.CARD, card_content=CardContent(title=f"Item {i}-3", body="Desc")),
        ]) for i in range(4)
    ]

    budget = DeckVisualBudget()
    for s in slides:
        selector.select_visual_for_slide(s, deck_budget=budget)

    # Verify history recorded all selections
    assert len(budget.archetype_history) == 4
