"""Deterministic geometric boundary and containment validation rules."""

from backend.app.layout.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from backend.app.layout.exceptions import GeometryValidationError
from backend.app.layout.models import ElementGeometry, LayoutWarning, Rect


def validate_rect_bounds(rect: Rect, element_id: str = "element", allow_canvas_bleed: bool = False) -> list[LayoutWarning]:
    """Validate that a rectangle conforms to physical canvas constraints."""
    warnings: list[LayoutWarning] = []

    if rect.width <= 0 or rect.height <= 0:
        raise GeometryValidationError(
            f"Element '{element_id}' has non-positive dimensions: {rect.width}x{rect.height}"
        )

    if not allow_canvas_bleed:
        if rect.x < 0 or rect.y < 0:
            warnings.append(
                LayoutWarning(
                    code="OUT_OF_BOUNDS_NEGATIVE",
                    message=f"Element '{element_id}' starts outside canvas at ({rect.x}, {rect.y})",
                    slide_id="current",
                    element_id=element_id,
                    severity="warning",
                )
            )

        if rect.right > CANVAS_WIDTH:
            overflow_px = rect.right - CANVAS_WIDTH
            warnings.append(
                LayoutWarning(
                    code="OVERFLOW_RIGHT",
                    message=f"Element '{element_id}' overflows canvas right by {overflow_px}px ({rect.right} > {CANVAS_WIDTH})",
                    slide_id="current",
                    element_id=element_id,
                    severity="warning",
                )
            )

        if rect.bottom > CANVAS_HEIGHT:
            overflow_px = rect.bottom - CANVAS_HEIGHT
            warnings.append(
                LayoutWarning(
                    code="OVERFLOW_BOTTOM",
                    message=f"Element '{element_id}' overflows canvas bottom by {overflow_px}px ({rect.bottom} > {CANVAS_HEIGHT})",
                    slide_id="current",
                    element_id=element_id,
                    severity="warning",
                )
            )

    return warnings


def validate_child_containment(
    parent_geom: ElementGeometry,
    child_geom: ElementGeometry,
) -> list[LayoutWarning]:
    """Verify that a child element fits within its container boundary."""
    warnings: list[LayoutWarning] = []
    p_rect = parent_geom.rect
    c_rect = child_geom.rect

    if not p_rect.contains_rect(c_rect):
        warnings.append(
            LayoutWarning(
                code="CHILD_OUTSIDE_PARENT",
                message=(
                    f"Child element '{child_geom.id}' [{c_rect.x},{c_rect.y},{c_rect.width}x{c_rect.height}] "
                    f"exceeds parent '{parent_geom.id}' [{p_rect.x},{p_rect.y},{p_rect.width}x{p_rect.height}]"
                ),
                slide_id="current",
                element_id=child_geom.id,
                severity="warning",
            )
        )

    return warnings


def clamp_rect_to_canvas(rect: Rect) -> Rect:
    """Safely clamp a rectangle so it stays strictly within the 1920x1080 canvas."""
    x = max(0, min(rect.x, CANVAS_WIDTH - 10))
    y = max(0, min(rect.y, CANVAS_HEIGHT - 10))
    max_w = CANVAS_WIDTH - x
    max_h = CANVAS_HEIGHT - y
    width = max(1, min(rect.width, max_w))
    height = max(1, min(rect.height, max_h))
    return Rect(x=x, y=y, width=width, height=height)
