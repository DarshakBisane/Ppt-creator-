"""Deterministic local geometric correction operators for Pass 1 auto-repair."""

from backend.app.domain.enums import ElementType
from backend.app.layout.constants import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CONTENT_BOTTOM,
    MAX_CONTAINER_EXPANSION_RATIO,
    MIN_BODY_FONT_SIZE,
    MIN_CAPTION_FONT_SIZE,
    SAFE_MARGIN_X,
    SAFE_MARGIN_Y,
)
from backend.app.layout.constraints import clamp_rect_to_canvas
from backend.app.layout.models import (
    ConnectorGeometry,
    ElementGeometry,
    Rect,
    SlideLayoutResult,
)
from backend.app.layout.spacing import generate_ports
from backend.app.visual_qa.connectors import snap_connector_endpoints
from backend.app.visual_qa.models import (
    CorrectionRecord,
    QAIssue,
    QAIssueType,
    QASeverity,
)
from backend.app.visual_qa.spatial import classify_layer


def apply_local_corrections(
    slide_layout: SlideLayoutResult,
    issues: list[QAIssue],
    pass_number: int = 1,
) -> tuple[SlideLayoutResult, list[CorrectionRecord]]:
    """Apply targeted, non-destructive geometric adjustments to repair detected issues in-place."""
    corrections: list[CorrectionRecord] = []
    element_map: dict[str, ElementGeometry] = {e.id: e.model_copy(deep=True) for e in slide_layout.elements}
    connectors: list[ConnectorGeometry] = [c.model_copy(deep=True) for c in slide_layout.connectors]

    for issue in issues:
        if issue.severity not in (QASeverity.CRITICAL, QASeverity.ERROR, QASeverity.WARNING):
            continue

        # 1. Repair INVALID_GEOMETRY or OUT_OF_BOUNDS
        if issue.issue_type in (QAIssueType.INVALID_GEOMETRY, QAIssueType.OUT_OF_BOUNDS, QAIssueType.UNSAFE_MARGIN):
            elem_id = issue.element_id
            if elem_id and elem_id in element_map:
                elem = element_map[elem_id]
                old_rect = elem.rect
                new_w = max(40, old_rect.width)
                new_h = max(30, old_rect.height)
                clamped_rect = clamp_rect_to_canvas(Rect(x=old_rect.x, y=old_rect.y, width=new_w, height=new_h))

                # Shift inside safe margin if needed
                if clamped_rect.x < SAFE_MARGIN_X and elem.role != "canvas":
                    clamped_rect = Rect(
                        x=SAFE_MARGIN_X,
                        y=clamped_rect.y,
                        width=min(clamped_rect.width, CANVAS_WIDTH - (SAFE_MARGIN_X * 2)),
                        height=clamped_rect.height,
                    )

                if clamped_rect != old_rect:
                    elem.rect = clamped_rect
                    elem.ports = generate_ports(elem.id, clamped_rect)
                    element_map[elem_id] = elem
                    corrections.append(
                        CorrectionRecord(
                            pass_number=pass_number,
                            issue_type=issue.issue_type,
                            strategy="clamp_rect_and_shift_margin",
                            element_id=elem_id,
                            description=f"Clamped rect ({old_rect.x},{old_rect.y},{old_rect.width}x{old_rect.height}) -> ({clamped_rect.x},{clamped_rect.y},{clamped_rect.width}x{clamped_rect.height})",
                            success=True,
                        )
                    )

        # 2. Repair TEXT_OVERFLOW or CONTAINMENT_VIOLATION via Container Expansion
        elif issue.issue_type in (QAIssueType.TEXT_OVERFLOW, QAIssueType.CONTAINMENT_VIOLATION):
            elem_id = issue.element_id
            if elem_id and elem_id in element_map:
                elem = element_map[elem_id]
                old_rect = elem.rect
                max_expansion = int(old_rect.height * MAX_CONTAINER_EXPANSION_RATIO)

                # Check if expansion is within slide content bottom boundary
                available_space = CONTENT_BOTTOM - old_rect.bottom
                expansion_px = min(max_expansion, max(0, available_space))

                if expansion_px > 5:
                    new_rect = Rect(
                        x=old_rect.x,
                        y=old_rect.y,
                        width=old_rect.width,
                        height=old_rect.height + expansion_px,
                    )
                    elem.rect = new_rect
                    elem.ports = generate_ports(elem.id, new_rect)
                    element_map[elem_id] = elem
                    corrections.append(
                        CorrectionRecord(
                            pass_number=pass_number,
                            issue_type=issue.issue_type,
                            strategy="expand_container_height",
                            element_id=elem_id,
                            description=f"Expanded container height by +{expansion_px}px (to {new_rect.height}px)",
                            success=True,
                        )
                    )

        # 3. Repair SIBLING_COLLISION via Spacing Adjustment
        elif issue.issue_type == QAIssueType.SIBLING_COLLISION:
            elem_id = issue.element_id
            related_ids = issue.related_element_ids
            if elem_id and related_ids and elem_id in element_map:
                rel_id = related_ids[0]
                if rel_id in element_map:
                    elem_a = element_map[elem_id]
                    elem_b = element_map[rel_id]

                    # If side-by-side horizontally, adjust widths and positions
                    if abs(elem_a.rect.y - elem_b.rect.y) < 50:
                        left_elem = elem_a if elem_a.rect.x <= elem_b.rect.x else elem_b
                        right_elem = elem_b if elem_a.rect.x <= elem_b.rect.x else elem_a
                        gap = 20
                        overlap_px = (left_elem.rect.right + gap) - right_elem.rect.x

                        if overlap_px > 0:
                            shrink_each = (overlap_px // 2) + 2
                            new_w_l = max(50, left_elem.rect.width - shrink_each)
                            new_w_r = max(50, right_elem.rect.width - shrink_each)
                            new_x_r = left_elem.rect.x + new_w_l + gap

                            left_elem.rect = Rect(x=left_elem.rect.x, y=left_elem.rect.y, width=new_w_l, height=left_elem.rect.height)
                            left_elem.ports = generate_ports(left_elem.id, left_elem.rect)
                            right_elem.rect = Rect(x=new_x_r, y=right_elem.rect.y, width=new_w_r, height=right_elem.rect.height)
                            right_elem.ports = generate_ports(right_elem.id, right_elem.rect)

                            element_map[left_elem.id] = left_elem
                            element_map[right_elem.id] = right_elem

                            corrections.append(
                                CorrectionRecord(
                                    pass_number=pass_number,
                                    issue_type=QAIssueType.SIBLING_COLLISION,
                                    strategy="adjust_sibling_card_spacing",
                                    element_id=elem_id,
                                    description=f"Adjusted sibling widths and gap (-{shrink_each}px each, gap={gap}px)",
                                    success=True,
                                )
                            )

        # 4. Repair CONNECTOR_INVALID via Port Snapping
        elif issue.issue_type in (QAIssueType.CONNECTOR_INVALID, QAIssueType.CONNECTOR_CONTENT_OVERLAP):
            conn_id = issue.element_id
            for idx, c in enumerate(connectors):
                if c.id == conn_id:
                    repaired_conn, was_repaired = snap_connector_endpoints(c, list(element_map.values()))
                    if was_repaired:
                        connectors[idx] = repaired_conn
                        corrections.append(
                            CorrectionRecord(
                                pass_number=pass_number,
                                issue_type=issue.issue_type,
                                strategy="snap_connector_ports",
                                element_id=conn_id,
                                description=f"Snapped connector endpoints to valid ports ({repaired_conn.start_x},{repaired_conn.start_y}) -> ({repaired_conn.end_x},{repaired_conn.end_y})",
                                success=True,
                            )
                        )

    updated_layout = slide_layout.model_copy(
        update={
            "elements": list(element_map.values()),
            "connectors": connectors,
        }
    )

    return updated_layout, corrections
