"""Slide visual information density analysis with archetype-aware thresholds."""

from backend.app.domain.enums import VisualType
from backend.app.layout.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from backend.app.layout.models import ElementGeometry
from backend.app.visual_qa.models import (
    DensityLevel,
    LayerCategory,
    QAIssue,
    QAIssueType,
    QASeverity,
    SlideDensityMetrics,
)
from backend.app.visual_qa.overflow import extract_element_text
from backend.app.visual_qa.spatial import classify_layer

# Total canvas surface area (1920 x 1080)
TOTAL_CANVAS_AREA: int = CANVAS_WIDTH * CANVAS_HEIGHT


def compute_slide_density(
    elements: list[ElementGeometry],
    visual_type: VisualType,
    slide_id: str,
    slide_index: int = 1,
) -> tuple[SlideDensityMetrics, list[QAIssue]]:
    """Deterministically analyze visual density, whitespace ratio, and content volume."""
    issues: list[QAIssue] = []

    # Filter out pure canvas background
    content_elements = [e for e in elements if classify_layer(e) != LayerCategory.BACKGROUND]
    element_count = len(content_elements)

    # Calculate occupied area (sum of content rects)
    occupied_area = sum(e.rect.width * e.rect.height for e in content_elements)
    occupied_ratio = min(1.0, max(0.0, occupied_area / TOTAL_CANVAS_AREA))
    whitespace_ratio = max(0.0, 1.0 - occupied_ratio)

    # Calculate character count
    total_chars = 0
    for e in content_elements:
        p_txt, s_txt = extract_element_text(e)
        total_chars += len(p_txt) + len(s_txt)

    # Archetype-aware density thresholds
    is_dense_archetype = visual_type in (
        VisualType.ARCHITECTURE,
        VisualType.TABLE,
        VisualType.FLOWCHART,
        VisualType.MATRIX,
        VisualType.HIERARCHY,
        VisualType.TREE,
    )
    is_sparse_archetype = visual_type in (
        VisualType.HERO,
        VisualType.QUOTE,
        VisualType.NONE,
    )

    # Classification
    if is_dense_archetype:
        critical_thresh = 0.88
        high_thresh = 0.75
        low_thresh = 0.20
        max_elem_warn = 26
    elif is_sparse_archetype:
        critical_thresh = 0.70
        high_thresh = 0.55
        low_thresh = 0.10
        max_elem_warn = 8
    else:
        critical_thresh = 0.82
        high_thresh = 0.68
        low_thresh = 0.18
        max_elem_warn = 18

    if occupied_ratio >= critical_thresh or element_count > (max_elem_warn + 6):
        density_level = DensityLevel.CRITICAL
    elif occupied_ratio >= high_thresh or element_count > max_elem_warn or total_chars > 900:
        density_level = DensityLevel.HIGH
    elif occupied_ratio <= low_thresh and element_count <= 2:
        density_level = DensityLevel.LOW
    else:
        density_level = DensityLevel.BALANCED

    is_balanced = density_level in (DensityLevel.BALANCED, DensityLevel.LOW)

    metrics = SlideDensityMetrics(
        occupied_area_ratio=round(occupied_ratio, 3),
        whitespace_ratio=round(whitespace_ratio, 3),
        element_count=element_count,
        content_count=len([e for e in content_elements if classify_layer(e) == LayerCategory.CONTENT]),
        character_count=total_chars,
        density_level=density_level,
        is_balanced=is_balanced,
    )

    if density_level == DensityLevel.CRITICAL:
        issues.append(
            QAIssue(
                issue_type=QAIssueType.DENSITY_HIGH,
                severity=QASeverity.WARNING,
                slide_id=slide_id,
                slide_index=slide_index,
                message=(
                    f"Slide visual density is CRITICAL: occupied area ratio is {occupied_ratio:.1%} "
                    f"with {element_count} elements and {total_chars} characters."
                ),
                measured_value=f"occupied={occupied_ratio:.1%}, elems={element_count}",
                expected_value=f"< {critical_thresh:.1%}",
                correction_strategy="condense_spacing_or_card_layout",
                is_correctable=True,
            )
        )
    elif density_level == DensityLevel.HIGH and not is_dense_archetype:
        issues.append(
            QAIssue(
                issue_type=QAIssueType.DENSITY_HIGH,
                severity=QASeverity.INFO,
                slide_id=slide_id,
                slide_index=slide_index,
                message=f"Slide visual density is HIGH ({occupied_ratio:.1%} occupied, {element_count} elements).",
                measured_value=f"{occupied_ratio:.1%}",
                expected_value=f"< {high_thresh:.1%}",
                correction_strategy="optimize_padding_and_margins",
                is_correctable=True,
            )
        )

    return metrics, issues
