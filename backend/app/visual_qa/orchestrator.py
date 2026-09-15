"""High-level Visual QA and Auto-Correction Orchestrator."""

from backend.app.domain.design_system import DesignSystem
from backend.app.domain.presentation import Presentation, Slide
from backend.app.layout.engine import LayoutEngine, default_layout_engine
from backend.app.layout.models import PresentationLayoutResult, SlideLayoutResult
from backend.app.visual_qa.analyzer import SlideVisualAnalyzer, default_slide_analyzer
from backend.app.visual_qa.correction_pass import (
    ThreePassCorrectionEngine,
    default_correction_engine,
)
from backend.app.visual_qa.models import (
    CorrectionRecord,
    PassRecord,
    QAIssue,
    QASeverity,
    SlideQAResult,
    VisualQAResult,
)


class VisualQAOrchestrator:
    """Production Visual Quality Assurance & Auto-Correction Orchestrator.
    
    Validates geometric integrity, readability, collisions, density, and structure
    across presentations, applying up to 3 deterministic correction passes with
    monotonic quality guarantees.
    """

    def __init__(
        self,
        analyzer: SlideVisualAnalyzer | None = None,
        correction_engine: ThreePassCorrectionEngine | None = None,
        layout_engine: LayoutEngine | None = None,
    ) -> None:
        self.analyzer = analyzer or default_slide_analyzer
        self.correction_engine = correction_engine or default_correction_engine
        self.layout_engine = layout_engine or default_layout_engine

    def validate_and_correct_slide(
        self,
        slide: Slide,
        slide_layout: SlideLayoutResult | None = None,
        design_system: DesignSystem | None = None,
    ) -> SlideQAResult:
        """Validate and auto-correct a single slide layout."""
        ds = design_system or DesignSystem()
        initial_layout = slide_layout or self.layout_engine.layout_slide(slide, ds)
        return self.correction_engine.correct_slide(slide, initial_layout, ds)

    def validate_and_correct_presentation(
        self,
        presentation: Presentation,
        layout_result: PresentationLayoutResult | None = None,
    ) -> VisualQAResult:
        """Validate and auto-correct an entire presentation layout bundle."""
        ds = presentation.design_system or DesignSystem()
        initial_layout = layout_result or self.layout_engine.layout_presentation(presentation)

        slide_results: list[SlideQAResult] = []
        all_corrections: list[CorrectionRecord] = []
        unresolved_issues: list[QAIssue] = []
        corrected_slides: list[SlideLayoutResult] = []

        total_critical = 0
        total_errors = 0
        total_warnings = 0
        max_passes_executed = 1

        for slide_model, slide_layout in zip(presentation.slides, initial_layout.slides):
            slide_qa = self.correction_engine.correct_slide(slide_model, slide_layout, ds)
            slide_results.append(slide_qa)
            corrected_slides.append(slide_qa.layout)
            all_corrections.extend(slide_qa.corrections_applied)

            # Tally metrics
            max_passes_executed = max(max_passes_executed, slide_qa.passes_executed)
            for issue in slide_qa.issues:
                if issue.severity == QASeverity.CRITICAL:
                    total_critical += 1
                    unresolved_issues.append(issue)
                elif issue.severity == QASeverity.ERROR:
                    total_errors += 1
                    unresolved_issues.append(issue)
                elif issue.severity == QASeverity.WARNING:
                    total_warnings += 1

        # Calculate presentation-level quality score
        if slide_results:
            avg_score = sum(s.quality_score for s in slide_results) / len(slide_results)
            final_quality_score = round(avg_score, 2)
        else:
            final_quality_score = 100.0

        all_passed = all(s.passed for s in slide_results)

        if all_passed and len(all_corrections) == 0 and total_warnings == 0:
            final_status = "PASSED"
        elif all_passed and len(all_corrections) > 0:
            final_status = "CORRECTED"
        elif all_passed and total_warnings > 0:
            final_status = "WARNINGS"
        else:
            final_status = "FAILED"

        validated_presentation_layout = PresentationLayoutResult(
            presentation_title=presentation.metadata.title,
            slides=corrected_slides,
            warnings=[
                w
                for s in corrected_slides
                for w in s.warnings
            ],
            canvas=ds.canvas or initial_layout.canvas,
        )

        return VisualQAResult(
            passed=all_passed,
            final_status=final_status,
            total_issues=total_critical + total_errors + total_warnings,
            critical_issues=total_critical,
            errors=total_errors,
            warnings=total_warnings,
            passes_executed=max_passes_executed,
            corrections_applied=all_corrections,
            final_quality_score=final_quality_score,
            slide_results=slide_results,
            unresolved_issues=unresolved_issues,
            correction_history=[],
            layout=validated_presentation_layout,
        )


# Global default orchestrator instance
default_qa_orchestrator = VisualQAOrchestrator()


def validate_and_correct_presentation(
    presentation: Presentation,
    layout_result: PresentationLayoutResult | None = None,
) -> VisualQAResult:
    """Convenience helper to run Visual QA and 3-Pass Auto-Correction across a presentation."""
    return default_qa_orchestrator.validate_and_correct_presentation(presentation, layout_result)


def validate_and_correct_slide(
    slide: Slide,
    slide_layout: SlideLayoutResult | None = None,
    design_system: DesignSystem | None = None,
) -> SlideQAResult:
    """Convenience helper to run Visual QA and 3-Pass Auto-Correction for a single slide."""
    return default_qa_orchestrator.validate_and_correct_slide(slide, slide_layout, design_system)
