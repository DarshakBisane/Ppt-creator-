"""Archetype-specific structural and semantic layout validation for all 18 visual archetypes."""

from backend.app.domain.enums import ElementType, VisualType
from backend.app.domain.presentation import Slide
from backend.app.layout.models import SlideLayoutResult
from backend.app.visual_qa.models import QAIssue, QAIssueType, QASeverity


def validate_archetype_structure(
    slide_layout: SlideLayoutResult,
    slide_model: Slide | None = None,
) -> list[QAIssue]:
    """Validate structural constraints and visual completeness for the resolved archetype."""
    issues: list[QAIssue] = []
    vtype = slide_layout.visual_type
    slide_id = slide_layout.slide_id
    slide_index = slide_layout.slide_number
    elements = slide_layout.elements
    connectors = slide_layout.connectors

    # 1. TIMELINE
    if vtype == VisualType.TIMELINE:
        milestones = [e for e in elements if "milestone" in e.id or "timeline" in e.id or e.role == "milestone"]
        if not milestones and len(elements) <= 3:
            # Only header elements present, no timeline nodes
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Timeline layout contains no milestone elements or axis cards.",
                    expected_value="At least 2 milestone nodes",
                    correction_strategy="relayout_with_process_flow_or_cards",
                    is_correctable=True,
                )
            )

    # 2. PROCESS FLOW
    elif vtype == VisualType.PROCESS_FLOW:
        steps = [e for e in elements if "step" in e.id or "process" in e.id or e.role == "process_step"]
        if not steps and len(elements) <= 3:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Process Flow layout contains no step elements.",
                    expected_value="At least 2 step elements",
                    correction_strategy="relayout_with_cards",
                    is_correctable=True,
                )
            )

    # 3. COMPARISON
    elif vtype == VisualType.COMPARISON:
        comp_cards = [e for e in elements if "comp_" in e.id or "column" in e.id or "side_" in e.id or e.role in ("left_option", "right_option", "comparison_card")]
        # Check that left and right cards are horizontally separated
        if len(comp_cards) >= 2:
            sorted_cards = sorted(comp_cards, key=lambda c: c.rect.x)
            card_left, card_right = sorted_cards[0], sorted_cards[1]
            if card_left.rect.right > card_right.rect.x:
                issues.append(
                    QAIssue(
                        issue_type=QAIssueType.ARCHETYPE_VIOLATION,
                        severity=QASeverity.ERROR,
                        slide_id=slide_id,
                        slide_index=slide_index,
                        element_id=card_left.id,
                        related_element_ids=[card_right.id],
                        message=f"Comparison columns overlap horizontally (left.right={card_left.rect.right} > right.x={card_right.rect.x})",
                        correction_strategy="adjust_comparison_columns",
                        is_correctable=True,
                    )
                )

    # 4. KPI DASHBOARD
    elif vtype == VisualType.KPI:
        kpi_elems = [e for e in elements if e.semantic_type == ElementType.KPI or "kpi" in e.id or e.role == "kpi_card"]
        if not kpi_elems:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="KPI Dashboard contains no KPI metric cards.",
                    correction_strategy="relayout_as_cards",
                    is_correctable=True,
                )
            )

    # 5. TABLE
    elif vtype == VisualType.TABLE:
        table_elems = [e for e in elements if e.semantic_type == ElementType.TABLE or "table" in e.id]
        if not table_elems:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Table archetype has no table geometry elements.",
                    correction_strategy="relayout_with_cards",
                    is_correctable=True,
                )
            )

    # 6. CHARTS (BAR, COLUMN, LINE, PIE, DONUT)
    elif vtype in (
        VisualType.BAR_CHART,
        VisualType.COLUMN_CHART,
        VisualType.LINE_CHART,
        VisualType.PIE_CHART,
        VisualType.DONUT_CHART,
    ):
        chart_elems = [e for e in elements if e.semantic_type == ElementType.CHART or "chart" in e.id]
        if not chart_elems:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message=f"Chart layout for visual type '{vtype.value}' contains no chart element.",
                    correction_strategy="fallback_to_kpi_or_cards",
                    is_correctable=True,
                )
            )

    # 7. ARCHITECTURE
    elif vtype == VisualType.ARCHITECTURE:
        arch_nodes = [e for e in elements if "arch_" in e.id or "layer_" in e.id or "tier_" in e.id or e.role in ("system_layer", "architecture_node")]
        if not arch_nodes and len(elements) <= 3:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Architecture archetype contains no system layers or node blocks.",
                    correction_strategy="relayout_as_flowchart_or_cards",
                    is_correctable=True,
                )
            )

    # 8. MATRIX
    elif vtype == VisualType.MATRIX:
        quadrants = [e for e in elements if "quadrant" in e.id or "cell_" in e.id or "matrix" in e.id]
        if not quadrants and len(elements) <= 3:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Matrix 2x2 layout is missing quadrant cards.",
                    correction_strategy="relayout_as_grid",
                    is_correctable=True,
                )
            )

    # 9. ROADMAP / CYCLE
    elif vtype in (VisualType.ROADMAP, VisualType.CYCLE):
        lanes = [e for e in elements if "lane" in e.id or "phase" in e.id or "stage" in e.id or "roadmap" in e.id]
        if not lanes and len(elements) <= 3:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Roadmap / Cycle layout contains no phase or swimlane structures.",
                    correction_strategy="relayout_as_timeline",
                    is_correctable=True,
                )
            )

    # 10. HIERARCHY / TREE / FLOWCHART / DIAGRAM
    elif vtype in (VisualType.HIERARCHY, VisualType.TREE, VisualType.FLOWCHART, VisualType.DIAGRAM):
        nodes = [e for e in elements if "node" in e.id or "tree" in e.id or "flow" in e.id or "step" in e.id]
        if not nodes and len(elements) <= 3:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message=f"Hierarchy/Flowchart layout for '{vtype.value}' has no structure nodes.",
                    correction_strategy="relayout_as_process_flow",
                    is_correctable=True,
                )
            )

    # 11. HERO / QUOTE / TITLE_BODY / CARD_GRID / BLANK
    elif vtype in (VisualType.HERO, VisualType.QUOTE, VisualType.TEXT, VisualType.CARD_GRID, VisualType.NONE):
        # Basic element presence
        if not elements:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.EMPTY_VISUAL,
                    severity=QASeverity.CRITICAL,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    message="Slide layout has 0 elements.",
                    correction_strategy="generate_default_canvas",
                    is_correctable=True,
                )
            )

    return issues
