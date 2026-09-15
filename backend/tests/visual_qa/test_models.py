"""Unit tests for Visual QA domain models and results."""

import pytest
from backend.app.domain.enums import NarrativeRole, VisualType
from backend.app.layout.models import PresentationLayoutResult, Rect, SlideLayoutResult
from backend.app.visual_qa.models import (
    CorrectionRecord,
    DensityLevel,
    LayerCategory,
    PassRecord,
    QAIssue,
    QAIssueType,
    QASeverity,
    SlideDensityMetrics,
    SlideQAResult,
    VisualQAResult,
)


def test_qa_severity_and_issue_type_enums() -> None:
    """Verify enum members exist and match expected values."""
    assert QASeverity.CRITICAL.value == "critical"
    assert QASeverity.ERROR.value == "error"
    assert QASeverity.WARNING.value == "warning"
    assert QASeverity.INFO.value == "info"

    assert QAIssueType.TEXT_OVERFLOW.value == "text_overflow"
    assert QAIssueType.SIBLING_COLLISION.value == "sibling_collision"
    assert QAIssueType.CONTAINMENT_VIOLATION.value == "containment_violation"
    assert QAIssueType.OUT_OF_BOUNDS.value == "out_of_bounds"
    assert QAIssueType.CONNECTOR_INVALID.value == "connector_invalid"


def test_qa_issue_model_instantiation() -> None:
    """Verify QAIssue instantiation with valid fields."""
    issue = QAIssue(
        issue_type=QAIssueType.TEXT_OVERFLOW,
        severity=QASeverity.ERROR,
        slide_id="slide_1",
        slide_index=1,
        element_id="card_1",
        related_element_ids=["card_2"],
        message="Text overflows container by 35px",
        measured_value="235px",
        expected_value="200px",
        correction_strategy="expand_container",
        is_correctable=True,
    )
    assert issue.issue_type == QAIssueType.TEXT_OVERFLOW
    assert issue.severity == QASeverity.ERROR
    assert issue.slide_id == "slide_1"
    assert issue.element_id == "card_1"
    assert issue.related_element_ids == ["card_2"]
    assert issue.is_correctable is True


def test_slide_qa_result_properties() -> None:
    """Verify SlideQAResult severity grouping properties."""
    crit_issue = QAIssue(
        issue_type=QAIssueType.INVALID_GEOMETRY,
        severity=QASeverity.CRITICAL,
        slide_id="s1",
        message="Non-positive rect",
    )
    err_issue = QAIssue(
        issue_type=QAIssueType.SIBLING_COLLISION,
        severity=QASeverity.ERROR,
        slide_id="s1",
        message="Collision between cards",
    )
    warn_issue = QAIssue(
        issue_type=QAIssueType.UNSAFE_MARGIN,
        severity=QASeverity.WARNING,
        slide_id="s1",
        message="Close to edge",
    )

    mock_layout = SlideLayoutResult(
        slide_id="s1",
        slide_number=1,
        visual_type=VisualType.CARD_GRID,
        narrative_role=NarrativeRole.SOLUTION,
        content_rect=Rect(x=100, y=200, width=1720, height=800),
    )

    result = SlideQAResult(
        slide_id="s1",
        slide_number=1,
        passed=False,
        visual_type=VisualType.CARD_GRID,
        archetype="three_card_row",
        quality_score=42.0,
        issues=[crit_issue, err_issue, warn_issue],
        density=SlideDensityMetrics(
            occupied_area_ratio=0.45,
            whitespace_ratio=0.55,
            element_count=5,
            content_count=3,
            character_count=200,
            density_level=DensityLevel.BALANCED,
            is_balanced=True,
        ),
        corrections_applied=[],
        passes_executed=1,
        layout=mock_layout,
    )

    assert len(result.critical_issues) == 1
    assert len(result.error_issues) == 1
    assert len(result.warning_issues) == 1
    assert result.passed is False


def test_visual_qa_result_aggregation() -> None:
    """Verify presentation-level VisualQAResult."""
    qa_res = VisualQAResult(
        passed=True,
        final_status="PASSED",
        total_issues=0,
        critical_issues=0,
        errors=0,
        warnings=0,
        passes_executed=1,
        final_quality_score=98.5,
    )
    assert qa_res.passed is True
    assert qa_res.final_status == "PASSED"
    assert qa_res.final_quality_score == 98.5
