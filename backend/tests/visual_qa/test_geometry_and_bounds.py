"""Unit tests for spatial geometry boundaries and canvas constraints."""

from backend.app.domain.enums import ElementType
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.models import QAIssueType, QASeverity
from backend.app.visual_qa.spatial import validate_element_geometry


def test_valid_element_geometry_passes() -> None:
    """A well-positioned element within canvas and safe margins generates 0 issues."""
    elem = ElementGeometry(
        id="valid_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=200, y=250, width=500, height=400),
        role="content",
    )
    issues = validate_element_geometry(elem, slide_id="s1")
    assert len(issues) == 0


def test_out_of_bounds_negative_coordinates() -> None:
    """An element starting at negative coordinates is flagged OUT_OF_BOUNDS."""
    elem = ElementGeometry(
        id="negative_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=-50, y=200, width=400, height=300),
    )
    issues = validate_element_geometry(elem, slide_id="s1")
    assert any(i.issue_type == QAIssueType.OUT_OF_BOUNDS and i.severity == QASeverity.ERROR for i in issues)


def test_out_of_bounds_canvas_overflow_right_and_bottom() -> None:
    """An element extending beyond 1920x1080 is flagged OUT_OF_BOUNDS."""
    elem = ElementGeometry(
        id="overflow_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=1600, y=800, width=500, height=400),  # right=2100 > 1920, bottom=1200 > 1080
    )
    issues = validate_element_geometry(elem, slide_id="s1")
    assert any(i.issue_type == QAIssueType.OUT_OF_BOUNDS and i.severity == QASeverity.ERROR for i in issues)


def test_unsafe_margin_warning() -> None:
    """Primary content positioned too close to outer canvas border generates an UNSAFE_MARGIN warning."""
    elem = ElementGeometry(
        id="edge_card",
        semantic_type=ElementType.CARD,
        rect=Rect(x=20, y=200, width=400, height=300),  # x=20 < 40px safe margin
        role="content",
    )
    issues = validate_element_geometry(elem, slide_id="s1")
    assert any(i.issue_type == QAIssueType.UNSAFE_MARGIN and i.severity == QASeverity.WARNING for i in issues)


def test_background_canvas_exempt_from_margin_warning() -> None:
    """Background canvas panels spanning the entire 1920x1080 canvas do not trigger UNSAFE_MARGIN."""
    bg_elem = ElementGeometry(
        id="s1_canvas_panel",
        semantic_type=ElementType.CARD,
        rect=Rect(x=0, y=0, width=1920, height=1080),
        role="canvas",
        z_index=-1,
    )
    issues = validate_element_geometry(bg_elem, slide_id="s1")
    assert not any(i.issue_type == QAIssueType.UNSAFE_MARGIN for i in issues)
