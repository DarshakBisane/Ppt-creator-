"""Spatial geometry validation, collision detection, and multi-layer classification."""

from backend.app.domain.enums import ElementType
from backend.app.layout.constants import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CONTENT_BOTTOM,
    CONTENT_TOP,
    HEADER_TOP,
    SAFE_MARGIN_X,
    SAFE_MARGIN_Y,
)
from backend.app.layout.models import ElementGeometry, Rect, SlideLayoutResult
from backend.app.visual_qa.models import LayerCategory, QAIssue, QAIssueType, QASeverity

# Default overlap tolerance in virtual units (ignore edge-touching <= 2px)
DEFAULT_COLLISION_TOLERANCE_PX: int = 2


def classify_layer(elem: ElementGeometry) -> LayerCategory:
    """Deterministically classify an element into its semantic layer category."""
    if elem.z_index < 0 or elem.role in ("canvas", "background", "canvas_panel"):
        return LayerCategory.BACKGROUND

    if elem.role in ("narrative_badge", "pill", "divider", "accent", "icon_accent"):
        return LayerCategory.DECORATION

    if elem.semantic_type in (ElementType.CARD, ElementType.GROUP):
        return LayerCategory.CONTAINER

    if elem.semantic_type == ElementType.CONNECTOR:
        return LayerCategory.CONNECTOR

    return LayerCategory.CONTENT


def validate_element_geometry(elem: ElementGeometry, slide_id: str, slide_index: int = 1) -> list[QAIssue]:
    """Validate that an individual element's geometry is positive and within canvas bounds."""
    issues: list[QAIssue] = []
    r = elem.rect

    # 1. Non-positive dimensions (CRITICAL)
    if r.width <= 0 or r.height <= 0:
        issues.append(
            QAIssue(
                issue_type=QAIssueType.INVALID_GEOMETRY,
                severity=QASeverity.CRITICAL,
                slide_id=slide_id,
                slide_index=slide_index,
                element_id=elem.id,
                message=f"Element '{elem.id}' has invalid non-positive dimensions ({r.width}x{r.height})",
                measured_value=f"{r.width}x{r.height}",
                expected_value="width > 0, height > 0",
                correction_strategy="clamp_or_recompute",
                is_correctable=True,
            )
        )
        return issues

    # 2. Out of Canvas Bounds (ERROR)
    if r.x < 0 or r.y < 0 or r.right > CANVAS_WIDTH or r.bottom > CANVAS_HEIGHT:
        overflow_x = max(0, -r.x) + max(0, r.right - CANVAS_WIDTH)
        overflow_y = max(0, -r.y) + max(0, r.bottom - CANVAS_HEIGHT)
        issues.append(
            QAIssue(
                issue_type=QAIssueType.OUT_OF_BOUNDS,
                severity=QASeverity.ERROR,
                slide_id=slide_id,
                slide_index=slide_index,
                element_id=elem.id,
                message=(
                    f"Element '{elem.id}' extends outside 1920x1080 canvas: "
                    f"rect=({r.x}, {r.y}, {r.width}x{r.height}), overflow=({overflow_x}px, {overflow_y}px)"
                ),
                measured_value=f"x={r.x}, y={r.y}, r={r.right}, b={r.bottom}",
                expected_value=f"[0, 0, {CANVAS_WIDTH}, {CANVAS_HEIGHT}]",
                correction_strategy="clamp_to_canvas",
                is_correctable=True,
            )
        )

    # 3. Unsafe Margins for Primary Content (WARNING)
    # Background and full-cover elements are exempt from margin checks
    layer = classify_layer(elem)
    if layer != LayerCategory.BACKGROUND and elem.role != "canvas":
        # Check if content touches extreme outer borders (< 40px from canvas edge)
        extreme_margin = 40
        if r.x < extreme_margin or r.right > (CANVAS_WIDTH - extreme_margin) or r.y < 30 or r.bottom > (CANVAS_HEIGHT - 30):
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.UNSAFE_MARGIN,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=elem.id,
                    message=f"Element '{elem.id}' encroaches into unsafe slide border margin zone",
                    measured_value=f"({r.x}, {r.y}, {r.right}, {r.bottom})",
                    expected_value=f"Safe zone >= {extreme_margin}px from edge",
                    correction_strategy="shift_inside_safe_margin",
                    is_correctable=True,
                )
            )

    return issues


def rect_intersection_area(r1: Rect, r2: Rect, tolerance_px: int = DEFAULT_COLLISION_TOLERANCE_PX) -> int:
    """Calculate the overlap area between two rects considering a tolerance buffer."""
    x_overlap = max(0, min(r1.right, r2.right) - max(r1.x, r2.x))
    y_overlap = max(0, min(r1.bottom, r2.bottom) - max(r1.y, r2.y))

    if x_overlap <= tolerance_px or y_overlap <= tolerance_px:
        return 0

    return x_overlap * y_overlap


def detect_collisions(
    elements: list[ElementGeometry],
    slide_id: str,
    slide_index: int = 1,
    tolerance_px: int = DEFAULT_COLLISION_TOLERANCE_PX,
) -> list[QAIssue]:
    """Deterministically detect invalid collisions between elements.
    
    Collision rules:
    - BACKGROUND elements never cause collisions.
    - Parent elements containing their children are containment, not collision.
    - Sibling CONTAINERS (e.g. cards, columns) must not collide.
    - Primary CONTENT must not collide with other primary CONTENT unless same container.
    - DECORATION elements must not obscure primary text CONTENT.
    """
    issues: list[QAIssue] = []
    sorted_elements = sorted(elements, key=lambda e: (e.z_index, e.rect.y, e.rect.x, e.id))
    n = len(sorted_elements)

    # Build parent-child hierarchy map
    parent_map: dict[str, str] = {}
    for elem in sorted_elements:
        if elem.parent_id:
            parent_map[elem.id] = elem.parent_id

    for i in range(n):
        elem_a = sorted_elements[i]
        layer_a = classify_layer(elem_a)

        if layer_a == LayerCategory.BACKGROUND:
            continue

        for j in range(i + 1, n):
            elem_b = sorted_elements[j]
            layer_b = classify_layer(elem_b)

            if layer_b == LayerCategory.BACKGROUND:
                continue

            # Check parent-child exemption
            if elem_a.id == elem_b.parent_id or elem_b.id == elem_a.parent_id:
                continue
            if parent_map.get(elem_a.id) and parent_map.get(elem_a.id) == elem_b.id:
                continue
            if parent_map.get(elem_b.id) and parent_map.get(elem_b.id) == elem_a.id:
                continue

            # Check if one rect strictly contains the other (handled by containment QA)
            if elem_a.rect.contains_rect(elem_b.rect) or elem_b.rect.contains_rect(elem_a.rect):
                continue

            # Calculate overlap
            overlap_area = rect_intersection_area(elem_a.rect, elem_b.rect, tolerance_px)
            if overlap_area <= 0:
                continue

            # Check collision severity by layer combination
            # 1. Sibling Containers Colliding (ERROR)
            if layer_a == LayerCategory.CONTAINER and layer_b == LayerCategory.CONTAINER:
                issues.append(
                    QAIssue(
                        issue_type=QAIssueType.SIBLING_COLLISION,
                        severity=QASeverity.ERROR,
                        slide_id=slide_id,
                        slide_index=slide_index,
                        element_id=elem_a.id,
                        related_element_ids=[elem_b.id],
                        message=f"Sibling containers '{elem_a.id}' and '{elem_b.id}' collide (overlap: {overlap_area}px²)",
                        measured_value=overlap_area,
                        expected_value=0,
                        correction_strategy="adjust_spacing_or_shrink_gaps",
                        is_correctable=True,
                    )
                )

            # 2. Content vs Content Colliding across different or no containers (ERROR)
            elif layer_a == LayerCategory.CONTENT and layer_b == LayerCategory.CONTENT:
                # If they share the same parent container and are both small badges or aligned text,
                # check if overlap is substantial
                issues.append(
                    QAIssue(
                        issue_type=QAIssueType.SIBLING_COLLISION,
                        severity=QASeverity.ERROR,
                        slide_id=slide_id,
                        slide_index=slide_index,
                        element_id=elem_a.id,
                        related_element_ids=[elem_b.id],
                        message=f"Primary content elements '{elem_a.id}' and '{elem_b.id}' overlap ({overlap_area}px²)",
                        measured_value=overlap_area,
                        expected_value=0,
                        correction_strategy="nudge_elements_or_reduce_font",
                        is_correctable=True,
                    )
                )

            # 3. Decoration obscuring primary content text (WARNING)
            elif (layer_a == LayerCategory.DECORATION and layer_b == LayerCategory.CONTENT) or (
                layer_b == LayerCategory.DECORATION and layer_a == LayerCategory.CONTENT
            ):
                content_id = elem_b.id if layer_a == LayerCategory.DECORATION else elem_a.id
                decor_id = elem_a.id if layer_a == LayerCategory.DECORATION else elem_b.id
                issues.append(
                    QAIssue(
                        issue_type=QAIssueType.SIBLING_COLLISION,
                        severity=QASeverity.WARNING,
                        slide_id=slide_id,
                        slide_index=slide_index,
                        element_id=content_id,
                        related_element_ids=[decor_id],
                        message=f"Decoration '{decor_id}' encroaches on content element '{content_id}' ({overlap_area}px²)",
                        measured_value=overlap_area,
                        expected_value=0,
                        correction_strategy="offset_decoration",
                        is_correctable=True,
                    )
                )

    return issues
