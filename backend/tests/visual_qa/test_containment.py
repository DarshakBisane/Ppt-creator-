"""Unit tests for parent-child containment hierarchy validation."""

from backend.app.domain.enums import ElementType
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.containment import validate_containment
from backend.app.visual_qa.models import QAIssueType, QASeverity


def test_child_inside_parent_passes() -> None:
    """A child element neatly bounded inside its parent container passes containment QA."""
    parent = ElementGeometry(
        id="card_1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=400),
    )
    child = ElementGeometry(
        id="card_1_title",
        semantic_type=ElementType.TEXT,
        parent_id="card_1",
        rect=Rect(x=124, y=224, width=452, height=60),
    )
    issues = validate_containment([parent, child], slide_id="s1")
    assert len(issues) == 0


def test_child_overflowing_parent_boundary_flagged() -> None:
    """A child extending below its parent bottom border triggers CONTAINMENT_VIOLATION."""
    parent = ElementGeometry(
        id="card_1",
        semantic_type=ElementType.CARD,
        rect=Rect(x=100, y=200, width=500, height=300),  # bottom=500
    )
    child = ElementGeometry(
        id="card_1_body",
        semantic_type=ElementType.TEXT,
        parent_id="card_1",
        rect=Rect(x=124, y=224, width=452, height=350),  # bottom=574 > 500
    )
    issues = validate_containment([parent, child], slide_id="s1")
    assert any(
        i.issue_type == QAIssueType.CONTAINMENT_VIOLATION and i.severity == QASeverity.ERROR
        for i in issues
    )


def test_child_with_missing_parent_id_flagged() -> None:
    """A child referencing a non-existent parent container ID triggers CONTAINMENT_VIOLATION."""
    child = ElementGeometry(
        id="orphan_text",
        semantic_type=ElementType.TEXT,
        parent_id="non_existent_card",
        rect=Rect(x=100, y=200, width=400, height=100),
    )
    issues = validate_containment([child], slide_id="s1")
    assert any(i.issue_type == QAIssueType.CONTAINMENT_VIOLATION for i in issues)
