"""Tests for basic layout archetypes (Blank, Title+Body, Hero, Two-Column, Three-Card, Four-Card)."""

import pytest

from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.layout.engine import LayoutEngine
from backend.app.layout.models import Rect


@pytest.fixture
def layout_engine() -> LayoutEngine:
    return LayoutEngine()


@pytest.fixture
def design_system() -> DesignSystem:
    return DesignSystem()


def test_blank_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_blank",
        slide_number=1,
        title="Blank Slide",
        narrative_role=NarrativeRole.CONTEXT,
        visual_plan=VisualPlan(visual_type=VisualType.NONE),
    )
    res = layout_engine.layout_slide(slide, design_system)
    assert res.slide_id == "s_blank"
    assert len(res.elements) >= 1
    # Check that panels are within canvas
    for elem in res.elements:
        assert elem.rect.x >= 0
        assert elem.rect.y >= 0
        assert elem.rect.right <= 1920
        assert elem.rect.bottom <= 1080


def test_title_body_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_tb",
        slide_number=2,
        title="Strategic Objectives",
        subtitle="Key outcomes for FY2026",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.TEXT),
        elements=[
            Element(id="e1", type=ElementType.TEXT, role="lead", text_content=TextContent(text="Lead paragraph overview")),
            Element(id="e2", type=ElementType.TEXT, role="bullet", text_content=TextContent(text="Core milestone 1")),
        ],
    )
    res = layout_engine.layout_slide(slide, design_system)
    assert res.header_rect is not None
    assert any(e.role == "lead" for e in res.elements)
    assert any(e.role == "body" for e in res.elements)
    assert any(e.role == "slide_title" for e in res.elements)


def test_hero_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_hero",
        slide_number=3,
        title="Next-Gen Architecture",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.HERO),
    )
    res = layout_engine.layout_slide(slide, design_system)
    hero_elem = next(e for e in res.elements if e.role == "hero")
    kpi_elem = next(e for e in res.elements if e.role == "kpi")
    assert hero_elem.rect.x < kpi_elem.rect.x
    assert hero_elem.rect.width > kpi_elem.rect.width


def test_two_column_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_two_col",
        slide_number=4,
        title="Decoupled Systems",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="col1", type=ElementType.CARD, card_content=CardContent(title="Left Col", body="Details A")),
            Element(id="col2", type=ElementType.CARD, card_content=CardContent(title="Right Col", body="Details B")),
        ],
    )
    res = layout_engine.layout_slide(slide, design_system)
    cols = [e for e in res.elements if e.role in ("column_left", "column_right", "card")]
    assert len(cols) == 2
    assert cols[0].rect.right < cols[1].rect.x  # Separated by column gap


def test_three_card_row_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_three_card",
        slide_number=5,
        title="Three Core Pillars",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="Pillar 1", body="Desc 1")),
            Element(id="c2", type=ElementType.CARD, card_content=CardContent(title="Pillar 2", body="Desc 2")),
            Element(id="c3", type=ElementType.CARD, card_content=CardContent(title="Pillar 3", body="Desc 3")),
        ],
    )
    res = layout_engine.layout_slide(slide, design_system)
    cards = [e for e in res.elements if e.semantic_type == ElementType.CARD and e.role == "card"]
    assert len(cards) == 3
    # Check cards are positioned left to right with uniform gap
    assert cards[0].rect.x < cards[1].rect.x < cards[2].rect.x
    gap1 = cards[1].rect.x - cards[0].rect.right
    gap2 = cards[2].rect.x - cards[1].rect.right
    assert gap1 == gap2


def test_four_card_grid_layout(layout_engine: LayoutEngine, design_system: DesignSystem) -> None:
    slide = Slide(
        id="s_four_card",
        slide_number=6,
        title="Capability Matrix",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="g1", type=ElementType.CARD, card_content=CardContent(title="Cap 1", body="Desc 1")),
            Element(id="g2", type=ElementType.CARD, card_content=CardContent(title="Cap 2", body="Desc 2")),
            Element(id="g3", type=ElementType.CARD, card_content=CardContent(title="Cap 3", body="Desc 3")),
            Element(id="g4", type=ElementType.CARD, card_content=CardContent(title="Cap 4", body="Desc 4")),
        ],
    )
    res = layout_engine.layout_slide(slide, design_system)
    grid_cards = [e for e in res.elements if e.role == "grid_cell"]
    assert len(grid_cards) == 4
    # Top row
    assert grid_cards[0].rect.y == grid_cards[1].rect.y
    # Bottom row
    assert grid_cards[2].rect.y == grid_cards[3].rect.y
    # Bottom row is below top row
    assert grid_cards[2].rect.y > grid_cards[0].rect.bottom
