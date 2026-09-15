"""Containment hierarchy validation ensuring child elements remain within parent bounds."""

from backend.app.layout.models import ElementGeometry, Rect
from backend.app.visual_qa.models import QAIssue, QAIssueType, QASeverity


def validate_containment(
    elements: list[ElementGeometry],
    slide_id: str,
    slide_index: int = 1,
) -> list[QAIssue]:
    """Verify that all child elements with a parent_id remain strictly inside their parent container."""
    issues: list[QAIssue] = []
    element_by_id: dict[str, ElementGeometry] = {elem.id: elem for elem in elements}

    # Sort elements deterministically
    sorted_elements = sorted(elements, key=lambda e: (e.rect.y, e.rect.x, e.id))

    for child in sorted_elements:
        if not child.parent_id:
            continue

        parent = element_by_id.get(child.parent_id)
        if not parent:
            # Parent referenced does not exist in slide layout
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.CONTAINMENT_VIOLATION,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=child.id,
                    related_element_ids=[child.parent_id],
                    message=f"Child element '{child.id}' references non-existent parent container '{child.parent_id}'",
                    correction_strategy="remove_parent_link",
                    is_correctable=True,
                )
            )
            continue

        p_rect = parent.rect
        c_rect = child.rect

        # Check containment
        if not p_rect.contains_rect(c_rect):
            # Calculate exact overflow amounts
            left_overflow = max(0, p_rect.x - c_rect.x)
            right_overflow = max(0, c_rect.right - p_rect.right)
            top_overflow = max(0, p_rect.y - c_rect.y)
            bottom_overflow = max(0, c_rect.bottom - p_rect.bottom)
            total_overflow = left_overflow + right_overflow + top_overflow + bottom_overflow

            issues.append(
                QAIssue(
                    issue_type=QAIssueType.CONTAINMENT_VIOLATION,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=child.id,
                    related_element_ids=[parent.id],
                    message=(
                        f"Child element '{child.id}' ({c_rect.x}, {c_rect.y}, {c_rect.width}x{c_rect.height}) "
                        f"exceeds parent container '{parent.id}' ({p_rect.x}, {p_rect.y}, {p_rect.width}x{p_rect.height}) "
                        f"by {total_overflow}px (dx_l={left_overflow}, dx_r={right_overflow}, dy_t={top_overflow}, dy_b={bottom_overflow})"
                    ),
                    measured_value=f"child_bottom={c_rect.bottom}, parent_bottom={p_rect.bottom}",
                    expected_value=f"child within parent [{p_rect.x}..{p_rect.right}, {p_rect.y}..{p_rect.bottom}]",
                    correction_strategy="fit_child_in_parent_or_expand",
                    is_correctable=True,
                )
            )

    return issues
