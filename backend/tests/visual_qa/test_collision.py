"""Unit tests for spatial collision detection across element layers."""

from backend.app.domain.enums import ElementType
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.models import QAIssueType, QASeverity
from backend.app.visual_qa.spatial import detect_collisions


def test_sibling_containers_overlapping_triggers_collision() -> None:
    """Two side-by-side cards overlapping by 80px triggers SIBLING_COLLISION ERROR."""
    card_a = ElementGeometry(
        id="card_left",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=400),
    )
    card_b = ElementGeometry(
        id="card_right",
        semantic_type=ElementType.CARD,
        rect=Rect(x=520, y=200, width=500, height=400),  # Overlaps card_a (left ends at 600 > 520)
    )
    issues = detect_collisions([card_a, card_b], slide_id="s1")
    assert any(i.issue_type == QAIssueType.SIBLING_COLLISION and i.severity == QASeverity.ERROR for i in issues)


def test_parent_containing_child_exempt_from_collision() -> None:
    """A card container containing a child text block is containment, not collision."""
    parent_card = ElementGeometry(
        id="parent_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=400),
    )
    child_text = ElementGeometry(
        id="child_text",
        semantic_type=ElementType.TEXT,
        parent_id="parent_card",
        rect=Rect(x=124, y=224, width=452, height=100),
    )
    issues = detect_collisions([parent_card, child_text], slide_id="s1")
    assert len(issues) == 0


def test_background_canvas_exempt_from_collision() -> None:
    """A full-bleed background shape spanning the slide never collides with foreground cards."""
    bg_elem = ElementGeometry(
        id="s1_bg",
        semantic_type=ElementType.SHAPE,
        role="canvas",
        z_index=-1,
        rect=Rect(x=0, y=0, width=1920, height=1080),
    )
    card_1 = ElementGeometry(
        id="card_1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=400),
    )
    card_2 = ElementGeometry(
        id="card_2",
        semantic_type=ElementType.CARD,
        rect=Rect(x=650, y=200, width=500, height=400),
    )
    issues = detect_collisions([bg_elem, card_1, card_2], slide_id="s1")
    assert len(issues) == 0


def test_touching_borders_within_tolerance_not_flagged() -> None:
    """Two cards touching exactly at x=600 with 1px border overlap is within tolerance."""
    card_a = ElementGeometry(
        id="card_1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=400),  # right=600
    )
    card_b = ElementGeometry(
        id="card_2",
        semantic_type=ElementType.CARD,
        rect=Rect(x=600, y=200, width=500, height=400),  # x=600
    )
    issues = detect_collisions([card_a, card_b], slide_id="s1", tolerance_px=2)
    assert len(issues) == 0
