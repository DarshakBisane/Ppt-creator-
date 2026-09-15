"""Unit tests for archetype-specific structural and semantic layout rules."""

from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.layout.models import ElementGeometry, Rect, SlideLayoutResult
from backend.app.visual_qa.archetype_rules import validate_archetype_structure
from backend.app.visual_qa.models import QAIssueType, QASeverity


def test_timeline_empty_visual_flagged() -> None:
    """Timeline layout containing 0 milestones is flagged as an EMPTY_VISUAL ERROR."""
    empty_timeline_layout = SlideLayoutResult(
        slide_id="s_timeline",
        slide_number=2,
        visual_type=VisualType.TIMELINE,
        narrative_role=NarrativeRole.TIMELINE,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
        elements=[],
    )
    issues = validate_archetype_structure(empty_timeline_layout)
    assert any(i.issue_type == QAIssueType.EMPTY_VISUAL and i.severity in (QASeverity.ERROR, QASeverity.CRITICAL) for i in issues)


def test_process_flow_valid_steps_pass() -> None:
    """Process Flow layout with step cards passes structural inspection."""
    step_1 = ElementGeometry(id="process_step_1", semantic_type=ElementType.CARD, role="process_step", rect=Rect(x=100, y=250, width=400, height=300))
    step_2 = ElementGeometry(id="process_step_2", semantic_type=ElementType.CARD, role="process_step", rect=Rect(x=600, y=250, width=400, height=300))
    step_3 = ElementGeometry(id="process_step_3", semantic_type=ElementType.CARD, role="process_step", rect=Rect(x=1100, y=250, width=400, height=300))

    layout = SlideLayoutResult(
        slide_id="s_process",
        slide_number=3,
        visual_type=VisualType.PROCESS_FLOW,
        narrative_role=NarrativeRole.PROCESS,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
        elements=[step_1, step_2, step_3],
    )
    issues = validate_archetype_structure(layout)
    assert len(issues) == 0


def test_comparison_overlapping_columns_flagged() -> None:
    """Comparison layout where left column overlaps into right column triggers ARCHETYPE_VIOLATION."""
    card_left = ElementGeometry(id="comp_left", semantic_type=ElementType.CARD, role="left_option", rect=Rect(x=100, y=200, width=900, height=600))  # right=1000
    card_right = ElementGeometry(id="comp_right", semantic_type=ElementType.CARD, role="right_option", rect=Rect(x=800, y=200, width=900, height=600)) # x=800 < 1000

    layout = SlideLayoutResult(
        slide_id="s_comp",
        slide_number=4,
        visual_type=VisualType.COMPARISON,
        narrative_role=NarrativeRole.COMPARISON,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
        elements=[card_left, card_right],
    )
    issues = validate_archetype_structure(layout)
    assert any(i.issue_type == QAIssueType.ARCHETYPE_VIOLATION for i in issues)


def test_kpi_dashboard_valid_metrics_pass() -> None:
    """KPI dashboard with KPI cards passes archetype validation."""
    kpi_1 = ElementGeometry(id="kpi_1", semantic_type=ElementType.KPI, role="kpi_card", rect=Rect(x=100, y=250, width=500, height=300))
    kpi_2 = ElementGeometry(id="kpi_2", semantic_type=ElementType.KPI, role="kpi_card", rect=Rect(x=650, y=250, width=500, height=300))

    layout = SlideLayoutResult(
        slide_id="s_kpi",
        slide_number=5,
        visual_type=VisualType.KPI,
        narrative_role=NarrativeRole.EVIDENCE,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
        elements=[kpi_1, kpi_2],
    )
    issues = validate_archetype_structure(layout)
    assert len(issues) == 0
