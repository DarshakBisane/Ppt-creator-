"""Deterministic 3-Pass Auto-Correction engine managing Pass 1, Pass 2, and Pass 3 with monotonic quality guarantees."""

from backend.app.domain.design_system import DesignSystem
from backend.app.domain.enums import Density, VisualType, WhitespacePreference
from backend.app.domain.presentation import Slide
from backend.app.layout.models import SlideLayoutResult
from backend.app.layout.resolver import SlideLayoutResolver
from backend.app.visual_intelligence.archetype_map import get_archetype_descriptor
from backend.app.visual_qa.analyzer import SlideVisualAnalyzer, default_slide_analyzer
from backend.app.visual_qa.corrections import apply_local_corrections
from backend.app.visual_qa.models import (
    CorrectionRecord,
    PassRecord,
    SlideQAResult,
)


class ThreePassCorrectionEngine:
    """Executes up to 3 deterministic auto-correction passes on a slide layout.
    
    Pass 1: Local In-Place Geometric Adjustments (container expansion, gap reduction, port snapping)
    Pass 2: Archetype Re-layout (recomputing geometry with compact spacing constraints)
    Pass 3: Semantic Fallback (switching to Phase 8 declared safe fallback archetype)
    """

    def __init__(
        self,
        analyzer: SlideVisualAnalyzer | None = None,
        resolver: SlideLayoutResolver | None = None,
    ) -> None:
        self.analyzer = analyzer or default_slide_analyzer
        self.resolver = resolver or SlideLayoutResolver()

    def correct_slide(
        self,
        slide: Slide,
        initial_layout: SlideLayoutResult,
        design_system: DesignSystem | None = None,
    ) -> SlideQAResult:
        """Execute the 3-pass correction sequence enforcing strict monotonicity."""
        ds = design_system or DesignSystem()
        pass_history: list[PassRecord] = []
        all_corrections: list[CorrectionRecord] = []

        # Step 0: Baseline Initial Analysis
        current_qa = self.analyzer.analyze(initial_layout, slide)
        best_qa = current_qa
        best_layout = initial_layout

        if current_qa.passed:
            return current_qa

        # -------------------------------------------------------------------
        # PASS 1: Local Geometric Correction
        # -------------------------------------------------------------------
        p1_layout, p1_corrections = apply_local_corrections(
            slide_layout=best_layout,
            issues=best_qa.issues,
            pass_number=1,
        )
        p1_qa = self.analyzer.analyze(p1_layout, slide)

        p1_accepted = p1_qa.quality_score >= best_qa.quality_score
        pass_history.append(
            PassRecord(
                pass_number=1,
                strategy_name="local_geometric_repair",
                score_before=best_qa.quality_score,
                score_after=p1_qa.quality_score,
                issues_count_before=len(best_qa.issues),
                issues_count_after=len(p1_qa.issues),
                accepted=p1_accepted,
                rationale="Applied container expansion, gap reduction, and port snapping",
            )
        )

        if p1_accepted:
            best_layout = p1_layout
            best_qa = p1_qa
            all_corrections.extend(p1_corrections)

        if best_qa.passed:
            return self._build_final_slide_result(best_qa, best_layout, all_corrections, passes_executed=1)

        # -------------------------------------------------------------------
        # PASS 2: Archetype Re-layout with Compact Spacing Context
        # -------------------------------------------------------------------
        compact_ds = ds.model_copy(deep=True)
        if compact_ds.layout_preferences:
            compact_ds.layout_preferences.density = Density.HIGH
            compact_ds.layout_preferences.whitespace_preference = WhitespacePreference.COMPACT

        p2_layout = self.resolver.resolve_slide(slide, compact_ds)
        p2_qa = self.analyzer.analyze(p2_layout, slide)

        p2_accepted = p2_qa.quality_score >= best_qa.quality_score
        pass_history.append(
            PassRecord(
                pass_number=2,
                strategy_name="archetype_relayout_compact",
                score_before=best_qa.quality_score,
                score_after=p2_qa.quality_score,
                issues_count_before=len(best_qa.issues),
                issues_count_after=len(p2_qa.issues),
                accepted=p2_accepted,
                rationale="Re-computed archetype geometry with compact spacing rules",
            )
        )

        if p2_accepted:
            best_layout = p2_layout
            best_qa = p2_qa
            all_corrections.append(
                CorrectionRecord(
                    pass_number=2,
                    issue_type=best_qa.issues[0].issue_type if best_qa.issues else "relayout",
                    strategy="compact_archetype_relayout",
                    description=f"Re-resolved slide with compact spacing (score: {p2_qa.quality_score})",
                    success=True,
                    score_delta=round(p2_qa.quality_score - best_qa.quality_score, 2),
                )
            )

        if best_qa.passed:
            return self._build_final_slide_result(best_qa, best_layout, all_corrections, passes_executed=2)

        # -------------------------------------------------------------------
        # PASS 3: Safe Semantic Fallback
        # -------------------------------------------------------------------
        descriptor = get_archetype_descriptor(slide.visual_plan.visual_type)
        fallback_vtype = descriptor.fallback_visual_type

        # If fallback is distinct from current visual type, re-resolve with fallback
        if fallback_vtype != slide.visual_plan.visual_type:
            fallback_slide = slide.model_copy(deep=True)
            fallback_slide.visual_plan.visual_type = fallback_vtype

            p3_layout = self.resolver.resolve_slide(fallback_slide, compact_ds)
            p3_qa = self.analyzer.analyze(p3_layout, fallback_slide)

            p3_accepted = p3_qa.quality_score >= best_qa.quality_score
            pass_history.append(
                PassRecord(
                    pass_number=3,
                    strategy_name=f"fallback_to_{fallback_vtype.value}",
                    score_before=best_qa.quality_score,
                    score_after=p3_qa.quality_score,
                    issues_count_before=len(best_qa.issues),
                    issues_count_after=len(p3_qa.issues),
                    accepted=p3_accepted,
                    rationale=f"Switched archetype to semantically compatible fallback '{fallback_vtype.value}'",
                )
            )

            if p3_accepted:
                best_layout = p3_layout
                best_qa = p3_qa
                all_corrections.append(
                    CorrectionRecord(
                        pass_number=3,
                        issue_type=best_qa.issues[0].issue_type if best_qa.issues else "fallback",
                        strategy=f"fallback_to_{fallback_vtype.value}",
                        description=f"Fell back to '{fallback_vtype.value}' archetype (score: {p3_qa.quality_score})",
                        success=True,
                        score_delta=round(p3_qa.quality_score - best_qa.quality_score, 2),
                    )
                )
        else:
            pass_history.append(
                PassRecord(
                    pass_number=3,
                    strategy_name="fallback_skipped",
                    score_before=best_qa.quality_score,
                    score_after=best_qa.quality_score,
                    issues_count_before=len(best_qa.issues),
                    issues_count_after=len(best_qa.issues),
                    accepted=False,
                    rationale="No distinct fallback archetype available",
                )
            )

        return self._build_final_slide_result(best_qa, best_layout, all_corrections, passes_executed=3)

    def _build_final_slide_result(
        self,
        qa_result: SlideQAResult,
        final_layout: SlideLayoutResult,
        corrections: list[CorrectionRecord],
        passes_executed: int,
    ) -> SlideQAResult:
        """Construct the final consolidated SlideQAResult."""
        return SlideQAResult(
            slide_id=qa_result.slide_id,
            slide_number=qa_result.slide_number,
            passed=qa_result.passed,
            visual_type=final_layout.visual_type,
            archetype=final_layout.metadata.get("archetype", str(final_layout.visual_type.value)),
            quality_score=qa_result.quality_score,
            issues=qa_result.issues,
            density=qa_result.density,
            corrections_applied=corrections,
            passes_executed=passes_executed,
            layout=final_layout,
        )


# Global default correction engine instance
default_correction_engine = ThreePassCorrectionEngine()
