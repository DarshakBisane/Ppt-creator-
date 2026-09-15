"""Semantic Visual Selector orchestrator selecting optimal visual models and refining presentations."""

from backend.app.ai.context import DesignContext
from backend.app.domain.enums import VisualType
from backend.app.domain.presentation import Presentation, Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.visual_intelligence.archetype_map import get_archetype_descriptor
from backend.app.visual_intelligence.classifier import ContentSemanticClassifier
from backend.app.visual_intelligence.data_builder import VisualDataBuilder
from backend.app.visual_intelligence.models import (
    CandidateScore,
    DeckVisualBudget,
    SemanticVisualDecision,
)
from backend.app.visual_intelligence.rules import VisualScoringEngine


class SemanticVisualSelector:
    """Production Semantic Visual Selection Engine.
    
    Transforms slide narrative intent and semantic content into optimal visual
    representations and Phase 6 layout archetypes while enforcing visual diversity budgets.
    """

    def __init__(self) -> None:
        self.classifier = ContentSemanticClassifier()
        self.scoring_engine = VisualScoringEngine()
        self.data_builder = VisualDataBuilder()

    def select_visual_for_slide(
        self,
        slide: Slide,
        design_context: DesignContext | None = None,
        deck_budget: DeckVisualBudget | None = None,
    ) -> SemanticVisualDecision:
        """Analyze slide content and select the most appropriate visual archetype."""
        # 1. Semantic Signal Extraction
        signal = self.classifier.classify_slide(slide)

        # 2. Candidate Evaluation & Deterministic Ranking
        candidates = self.scoring_engine.evaluate_candidates(
            signal=signal,
            narrative_role=slide.narrative_role,
            design_context=design_context,
            deck_budget=deck_budget,
        )

        top_candidate = candidates[0]
        vtype = top_candidate.visual_type
        descriptor = get_archetype_descriptor(vtype)

        # 3. Data Requirement Validation & Fallback Handling
        selected_vtype = vtype
        selected_archetype = top_candidate.archetype
        fallback_vtype = descriptor.fallback_visual_type
        fallback_archetype = descriptor.fallback_archetype
        rationale = top_candidate.rationale

        # Verify complex data requirements
        if vtype == VisualType.TIMELINE:
            timeline_data = self.data_builder.build_timeline_data(slide)
            if not timeline_data:
                # Fallback to Process Flow or Card Grid
                selected_vtype = fallback_vtype
                selected_archetype = fallback_archetype
                rationale += f" [Data check failed -> fallback to {fallback_vtype.value}]"

        elif vtype == VisualType.PROCESS_FLOW:
            process_data = self.data_builder.build_process_flow_data(slide)
            if not process_data:
                selected_vtype = fallback_vtype
                selected_archetype = fallback_archetype
                rationale += f" [Data check failed -> fallback to {fallback_vtype.value}]"

        elif vtype == VisualType.TABLE:
            table_data = self.data_builder.build_table_data(slide)
            if not table_data:
                selected_vtype = fallback_vtype
                selected_archetype = fallback_archetype
                rationale += f" [Data check failed -> fallback to {fallback_vtype.value}]"

        elif descriptor.requires_quantitative_data:
            chart_type_map = {
                VisualType.LINE_CHART: "line",
                VisualType.COLUMN_CHART: "column",
                VisualType.BAR_CHART: "bar",
                VisualType.PIE_CHART: "pie",
                VisualType.DONUT_CHART: "donut",
            }
            if vtype in chart_type_map:
                chart_data = self.data_builder.build_chart_data(slide, chart_type_map[vtype])
                if not chart_data and not (slide.visual_plan and slide.visual_plan.chart_data):
                    selected_vtype = fallback_vtype
                    selected_archetype = fallback_archetype
                    rationale += f" [Quantitative data missing -> fallback to {fallback_vtype.value}]"

        # 4. Record decision in budget
        if deck_budget:
            deck_budget.record_selection(selected_vtype, selected_archetype)

        return SemanticVisualDecision(
            selected_visual_type=selected_vtype,
            selected_archetype=selected_archetype,
            rationale=rationale,
            confidence=signal.confidence,
            requires_quantitative_data=descriptor.requires_quantitative_data,
            fallback_visual_type=fallback_vtype,
            fallback_archetype=fallback_archetype,
            candidate_rankings=candidates[:5],
        )

    def refine_slide(
        self,
        slide: Slide,
        design_context: DesignContext | None = None,
        deck_budget: DeckVisualBudget | None = None,
    ) -> Slide:
        """Refine a single slide's VisualPlan with semantic visual selection decisions."""
        decision = self.select_visual_for_slide(slide, design_context, deck_budget)

        vp = slide.visual_plan or VisualPlan()
        vp.visual_type = decision.selected_visual_type
        vp.intent = decision.rationale

        # Attach domain data payloads if selected
        if decision.selected_visual_type == VisualType.TIMELINE and not vp.timeline_data:
            vp.timeline_data = self.data_builder.build_timeline_data(slide)

        elif decision.selected_visual_type == VisualType.PROCESS_FLOW and not vp.process_flow_data:
            vp.process_flow_data = self.data_builder.build_process_flow_data(slide)

        elif decision.selected_visual_type == VisualType.TABLE and not vp.table_data:
            vp.table_data = self.data_builder.build_table_data(slide)

        elif decision.selected_visual_type == VisualType.LINE_CHART and not vp.chart_data:
            vp.chart_data = self.data_builder.build_chart_data(slide, "line")

        elif decision.selected_visual_type in (VisualType.COLUMN_CHART, VisualType.BAR_CHART) and not vp.chart_data:
            vp.chart_data = self.data_builder.build_chart_data(
                slide,
                "column" if decision.selected_visual_type == VisualType.COLUMN_CHART else "bar",
            )

        slide.visual_plan = vp
        return slide

    def refine_presentation(
        self,
        presentation: Presentation,
        design_context: DesignContext | None = None,
    ) -> Presentation:
        """Refine an entire Presentation deck ensuring balanced visual variety and data integrity."""
        budget = DeckVisualBudget()
        refined_slides: list[Slide] = []

        for slide in presentation.slides:
            refined = self.refine_slide(slide, design_context, budget)
            refined_slides.append(refined)

        presentation.slides = refined_slides
        return presentation


# Global default selector instance
default_visual_selector = SemanticVisualSelector()


def select_presentation_visuals(
    presentation: Presentation,
    design_context: DesignContext | None = None,
) -> Presentation:
    """Convenience helper to refine all slides in a Presentation."""
    return default_visual_selector.refine_presentation(presentation, design_context)
