"""Tests for boundary constraints, attachment ports, and text fitting."""

import pytest

from backend.app.layout.constraints import validate_child_containment, validate_rect_bounds
from backend.app.layout.exceptions import GeometryValidationError
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.layout.spacing import generate_ports
from backend.app.layout.text_measurer import estimate_text_dimensions, fit_text_in_rect


def test_rect_boundary_validation() -> None:
    """Verify valid and invalid rect bounds detection."""
    # Valid rect within 1920x1080
    valid_rect = Rect(x=100, y=100, width=500, height=300)
    warnings = validate_rect_bounds(valid_rect)
    assert len(warnings) == 0

    # Negative coordinates
    neg_rect = Rect(x=-50, y=100, width=400, height=200)
    neg_warnings = validate_rect_bounds(neg_rect)
    assert any(w.code == "OUT_OF_BOUNDS_NEGATIVE" for w in neg_warnings)

    # Overflow right
    overflow_r = Rect(x=1800, y=100, width=300, height=200)
    r_warnings = validate_rect_bounds(overflow_r)
    assert any(w.code == "OVERFLOW_RIGHT" for w in r_warnings)

    # Overflow bottom
    overflow_b = Rect(x=100, y=1000, width=300, height=200)
    b_warnings = validate_rect_bounds(overflow_b)
    assert any(w.code == "OVERFLOW_BOTTOM" for w in b_warnings)


def test_connector_ports_placement() -> None:
    """Verify standard connector ports match exact border midpoint coordinates."""
    rect = Rect(x=100, y=200, width=400, height=300)
    ports = generate_ports("elem_1", rect)

    port_map = {p.side: (p.x, p.y) for p in ports}

    # Center X = 300, Center Y = 350
    assert port_map["top"] == (300, 200)
    assert port_map["bottom"] == (300, 500)
    assert port_map["left"] == (100, 350)
    assert port_map["right"] == (500, 350)
    assert port_map["center"] == (300, 350)


def test_child_containment_validation() -> None:
    """Verify child container boundary validation."""
    parent_geom = ElementGeometry(
        id="parent",
        semantic_type="card",
        rect=Rect(x=100, y=100, width=400, height=400),
    )

    # Child fits inside
    inside_child = ElementGeometry(
        id="child_in",
        semantic_type="text",
        rect=Rect(x=120, y=120, width=360, height=100),
    )
    assert len(validate_child_containment(parent_geom, inside_child)) == 0

    # Child exceeds parent boundary
    outside_child = ElementGeometry(
        id="child_out",
        semantic_type="text",
        rect=Rect(x=120, y=120, width=450, height=100),
    )
    warnings = validate_child_containment(parent_geom, outside_child)
    assert len(warnings) == 1
    assert warnings[0].code == "CHILD_OUTSIDE_PARENT"


def test_text_fitting_and_expansion() -> None:
    """Verify text container expansion and gradual font reduction."""
    target_rect = Rect(x=100, y=100, width=300, height=60)
    text = "This is a moderately long sentence requiring multiple lines."

    fitted_rect, font_size, warnings = fit_text_in_rect(
        text=text,
        target_rect=target_rect,
        initial_font_size=18,
        min_font_size=14,
        allow_expansion=True,
    )

    assert fitted_rect.width == target_rect.width
    assert font_size >= 14
    # Bounding box should either have expanded slightly or font size was reduced
    assert fitted_rect.height >= target_rect.height


def test_text_overflow_warning_on_huge_content() -> None:
    """Verify structured warning generation when text cannot fit."""
    small_rect = Rect(x=100, y=100, width=150, height=30)
    huge_text = "Word " * 200  # 1000 characters

    _, font_size, warnings = fit_text_in_rect(
        text=huge_text,
        target_rect=small_rect,
        initial_font_size=16,
        min_font_size=14,
        allow_expansion=False,
    )

    assert font_size == 14
    assert any(w.code == "TEXT_OVERFLOW_WARNING" for w in warnings)
