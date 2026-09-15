"""Visual QA Analyzer coordinating spatial, containment, overflow, density, and archetype diagnostics."""

from backend.app.domain.presentation import Presentation, Slide
from backend.app.layout.models import PresentationLayoutResult, SlideLayoutResult
from backend.app.visual_qa.archetype_rules import validate_archetype_structure
from backend.app.visual_qa.connectors import validate_connectors
from backend.app.visual_qa.containment import validate_containment
from backend.app.visual_qa.density import compute_slide_density
from backend.app.visual_qa.models import (
    DensityLevel,
    QAIssue,
    QAIssueType,
    QASeverity,
    SlideDensityMetrics,
    SlideQAResult,
    VisualQAResult,
)
from backend.app.visual_qa.overflow import validate_text_overflow
from backend.app.visual_qa.spatial import (
    detect_collisions,
    validate_element_geometry,
)


def calculate_quality_score(issues: list[QAIssue], density: SlideDensityMetrics) -> float:
    """Calculate a deterministic visual quality score from 0.0 to 100.0.
    
    Formula:
    Score = 100.0 - (40.0 * n_critical) - (15.0 * n_error) - (3.0 * n_warning) - (0.5 * n_info) - density_penalties
    Clamped strictly to [0.0, 100.0].
    """
    score = 100.0

    for issue in issues:
        if issue.severity == QASeverity.CRITICAL:
            score -= 40.0
        elif issue.severity == QASeverity.ERROR:
            score -= 15.0
        elif issue.severity == QASeverity.WARNING:
            score -= 3.0
        elif issue.severity == QASeverity.INFO:
            score -= 0.5

    # Density penalties
    if density.density_level == DensityLevel.CRITICAL:
        score -= 5.0
    elif density.density_level == DensityLevel.HIGH:
        score -= 2.0

    return max(0.0, min(100.0, round(score, 2)))


def sort_issues_deterministically(issues: list[QAIssue]) -> list[QAIssue]:
    """Sort QA issues deterministically by severity priority, issue type, and element ID."""
    severity_rank = {
        QASeverity.CRITICAL: 0,
        QASeverity.ERROR: 1,
        QASeverity.WARNING: 2,
        QASeverity.INFO: 3,
    }
    return sorted(
        issues,
        key=lambda i: (
            severity_rank.get(i.severity, 99),
            i.issue_type.value,
            i.element_id or "",
            i.message,
        ),
    )


class SlideVisualAnalyzer:
    """Analyzes a SlideLayoutResult across all visual and geometric QA dimensions."""

    def analyze(
        self,
        slide_layout: SlideLayoutResult,
        slide_model: Slide | None = None,
    ) -> SlideQAResult:
        """Run comprehensive QA inspection on a single slide layout."""
        all_issues: list[QAIssue] = []
        slide_id = slide_layout.slide_id
        slide_index = slide_layout.slide_number
        elements = slide_layout.elements

        # 1. Individual Element Geometry Bounds (Non-positive, Out of Bounds, Unsafe Margins)
        for elem in elements:
            geom_issues = validate_element_geometry(elem, slide_id, slide_index)
            all_issues.extend(geom_issues)

        # 2. Multi-layer Spatial Collision Detection
        collision_issues = detect_collisions(elements, slide_id, slide_index)
        all_issues.extend(collision_issues)

        # 3. Parent-Child Containment Validation
        containment_issues = validate_containment(elements, slide_id, slide_index)
        all_issues.extend(containment_issues)

        # 4. Text Capacity & Font-Size Overflow QA
        overflow_issues = validate_text_overflow(elements, slide_id, slide_index)
        all_issues.extend(overflow_issues)

        # 5. Connector Endpoint & Obstruction QA
        connector_issues = validate_connectors(slide_layout.connectors, elements, slide_id, slide_index)
        all_issues.extend(connector_issues)

        # 6. Archetype Structural Rules
        archetype_issues = validate_archetype_structure(slide_layout, slide_model)
        all_issues.extend(archetype_issues)

        # 7. Slide Visual Density Analysis
        density_metrics, density_issues = compute_slide_density(
            elements=elements,
            visual_type=slide_layout.visual_type,
            slide_id=slide_id,
            slide_index=slide_index,
        )
        all_issues.extend(density_issues)

        # 8. Sort issues and compute quality score
        sorted_issues = sort_issues_deterministically(all_issues)
        quality_score = calculate_quality_score(sorted_issues, density_metrics)

        # Passed condition: zero criticals, zero errors, score >= 70.0
        critical_count = sum(1 for i in sorted_issues if i.severity == QASeverity.CRITICAL)
        error_count = sum(1 for i in sorted_issues if i.severity == QASeverity.ERROR)
        passed = (critical_count == 0) and (error_count == 0) and (quality_score >= 70.0)

        return SlideQAResult(
            slide_id=slide_id,
            slide_number=slide_index,
            passed=passed,
            visual_type=slide_layout.visual_type,
            archetype=slide_layout.metadata.get("archetype", str(slide_layout.visual_type.value)),
            quality_score=quality_score,
            issues=sorted_issues,
            density=density_metrics,
            corrections_applied=[],
            passes_executed=1,
            layout=slide_layout,
        )


# Global default analyzer instance
default_slide_analyzer = SlideVisualAnalyzer()


def analyze_slide_layout(
    slide_layout: SlideLayoutResult,
    slide_model: Slide | None = None,
) -> SlideQAResult:
    """Convenience helper to analyze a single slide layout."""
    return default_slide_analyzer.analyze(slide_layout, slide_model)
