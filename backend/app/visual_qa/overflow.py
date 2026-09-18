"""Text measurement, container capacity, and font-size boundary QA."""

from backend.app.domain.content import CardContent, KPIContent, TextContent
from backend.app.domain.enums import ElementType
from backend.app.layout.constants import (
    MAX_CONTAINER_EXPANSION_RATIO,
    MIN_BODY_FONT_SIZE,
    MIN_CAPTION_FONT_SIZE,
)
from backend.app.layout.models import ElementGeometry, Rect
from backend.app.layout.text_measurer import estimate_text_dimensions
from backend.app.visual_qa.models import QAIssue, QAIssueType, QASeverity


def extract_element_text(elem: ElementGeometry) -> tuple[str, str]:
    """Extract primary text and secondary/subtitle text from element content data."""
    text_primary = ""
    text_secondary = ""

    if elem.content_data:
        data = elem.content_data
        if isinstance(data, dict):
            text_primary = str(data.get("title") or data.get("text") or data.get("value") or "")
            text_secondary = str(data.get("body") or data.get("label") or data.get("description") or data.get("context") or "")
        elif isinstance(data, TextContent):
            text_primary = data.text
        elif isinstance(data, CardContent):
            text_primary = data.title
            text_secondary = data.body
        elif isinstance(data, KPIContent):
            text_primary = data.value
            text_secondary = f"{data.label} {data.context or ''}"

    return text_primary.strip(), text_secondary.strip()


def validate_text_overflow(
    elements: list[ElementGeometry],
    slide_id: str,
    slide_index: int = 1,
) -> list[QAIssue]:
    """Validate that text inside elements fits within their geometric boundaries."""
    issues: list[QAIssue] = []
    sorted_elements = sorted(elements, key=lambda e: (e.rect.y, e.rect.x, e.id))

    for elem in sorted_elements:
        primary_txt, secondary_txt = extract_element_text(elem)
        combined_text = f"{primary_txt} {secondary_txt}".strip()
        if not combined_text:
            continue

        r = elem.rect
        # Internal padding allowance based on semantic type
        if elem.semantic_type == ElementType.CARD:
            pad_x, pad_y = 24, 24
        elif elem.semantic_type in (ElementType.TEXT, ElementType.HEADING):
            pad_x, pad_y = 4, 2
        else:
            pad_x, pad_y = 6, 4
        available_w = max(10, r.width - (pad_x * 2))
        available_h = max(10, r.height - (pad_y * 2))

        # Check font size bounds based on element role
        is_caption = elem.role in ("caption", "footnote", "context", "badge", "narrative_badge", "slide_subtitle", "subtitle")
        min_font = MIN_CAPTION_FONT_SIZE if is_caption else MIN_BODY_FONT_SIZE
        target_font = 20 if elem.semantic_type == ElementType.CARD else (28 if elem.semantic_type == ElementType.HEADING else 15)

        # Estimate required dimensions at target and minimum font sizes
        _, required_h_target, line_count = estimate_text_dimensions(
            text=combined_text,
            font_size=target_font,
            max_width=available_w,
        )

        _, required_h_min, min_lines = estimate_text_dimensions(
            text=combined_text,
            font_size=min_font,
            max_width=available_w,
        )

        # Check if text overflows even at minimum font size
        if required_h_min > available_h:
            overflow_h = required_h_min - available_h
            severity = QASeverity.CRITICAL if overflow_h > (available_h * 0.4) else (
                QASeverity.ERROR if overflow_h > 20 else QASeverity.WARNING
            )

            issues.append(
                QAIssue(
                    issue_type=QAIssueType.TEXT_OVERFLOW,
                    severity=severity,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=elem.id,
                    message=(
                        f"Text in element '{elem.id}' exceeds container height capacity: "
                        f"requires {required_h_min}px at minimum font ({min_font}pt), "
                        f"available height is {available_h}px (overflow: +{overflow_h}px, ~{min_lines} lines)"
                    ),
                    measured_value=f"required_h={required_h_min}px at {min_font}pt",
                    expected_value=f"available_h={available_h}px",
                    correction_strategy="expand_container_or_reduce_font",
                    is_correctable=True,
                )
            )

        elif required_h_target > available_h:
            # Fits at minimum font size, but requires font reduction
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.TEXT_OVERFLOW,
                    severity=QASeverity.INFO,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=elem.id,
                    message=(
                        f"Text in element '{elem.id}' fits comfortably with font reduction "
                        f"from {target_font}pt to intermediate size."
                    ),
                    measured_value=f"target_h={required_h_target}px",
                    expected_value=f"available_h={available_h}px",
                    correction_strategy="reduce_font_size",
                    is_correctable=True,
                )
            )

    return issues
