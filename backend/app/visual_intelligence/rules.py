"""Deterministic scoring and evaluation rules for candidate visual archetypes."""

from backend.app.ai.context import DesignContext
from backend.app.domain.enums import NarrativeRole, VisualType
from backend.app.visual_intelligence.archetype_map import (
    ARCHETYPE_MAPPINGS,
    get_archetype_descriptor,
    resolve_card_grid_archetype,
)
from backend.app.visual_intelligence.models import (
    CandidateScore,
    DeckVisualBudget,
    SemanticCategory,
    SemanticSignal,
)

# Mapping from VisualType to primary SemanticCategory
VISUAL_CATEGORY_AFFINITY: dict[VisualType, SemanticCategory] = {
    VisualType.TIMELINE: SemanticCategory.TEMPORAL,
    VisualType.ROADMAP: SemanticCategory.TEMPORAL,
    VisualType.PROCESS_FLOW: SemanticCategory.SEQUENTIAL,
    VisualType.FLOWCHART: SemanticCategory.SEQUENTIAL,
    VisualType.CYCLE: SemanticCategory.SEQUENTIAL,
    VisualType.HIERARCHY: SemanticCategory.HIERARCHICAL,
    VisualType.TREE: SemanticCategory.HIERARCHICAL,
    VisualType.COMPARISON: SemanticCategory.COMPARATIVE,
    VisualType.MATRIX: SemanticCategory.COMPARATIVE,
    VisualType.KPI: SemanticCategory.QUANTITATIVE,
    VisualType.LINE_CHART: SemanticCategory.QUANTITATIVE,
    VisualType.COLUMN_CHART: SemanticCategory.QUANTITATIVE,
    VisualType.BAR_CHART: SemanticCategory.QUANTITATIVE,
    VisualType.PIE_CHART: SemanticCategory.QUANTITATIVE,
    VisualType.DONUT_CHART: SemanticCategory.QUANTITATIVE,
    VisualType.ARCHITECTURE: SemanticCategory.RELATIONAL,
    VisualType.DIAGRAM: SemanticCategory.RELATIONAL,
    VisualType.TABLE: SemanticCategory.TABULAR,
    VisualType.QUOTE: SemanticCategory.KEY_STATEMENT,
    VisualType.HERO: SemanticCategory.KEY_STATEMENT,
    VisualType.CARD_GRID: SemanticCategory.CATEGORICAL,
    VisualType.TEXT: SemanticCategory.PROSE,
    VisualType.NONE: SemanticCategory.PROSE,
}

# Role bonuses
ROLE_BONUSES: dict[NarrativeRole, list[VisualType]] = {
    NarrativeRole.TITLE: [VisualType.HERO, VisualType.QUOTE],
    NarrativeRole.PROBLEM: [VisualType.HERO, VisualType.COMPARISON, VisualType.CARD_GRID],
    NarrativeRole.CONTEXT: [VisualType.KPI, VisualType.COLUMN_CHART, VisualType.CARD_GRID],
    NarrativeRole.PROCESS: [VisualType.PROCESS_FLOW, VisualType.FLOWCHART],
    NarrativeRole.TIMELINE: [VisualType.TIMELINE, VisualType.ROADMAP],
    NarrativeRole.COMPARISON: [VisualType.COMPARISON, VisualType.MATRIX, VisualType.TABLE],
    NarrativeRole.EVIDENCE: [VisualType.KPI, VisualType.COLUMN_CHART, VisualType.LINE_CHART, VisualType.TABLE],
    NarrativeRole.SOLUTION: [VisualType.CARD_GRID, VisualType.ARCHITECTURE],
    NarrativeRole.ARCHITECTURE: [VisualType.ARCHITECTURE, VisualType.FLOWCHART],
    NarrativeRole.SUMMARY: [VisualType.KPI, VisualType.CARD_GRID],
    NarrativeRole.CONCLUSION: [VisualType.HERO, VisualType.QUOTE],
    NarrativeRole.CALL_TO_ACTION: [VisualType.HERO, VisualType.CARD_GRID],
}


class VisualScoringEngine:
    """Evaluates and ranks all candidate visual archetypes deterministically."""

    def evaluate_candidates(
        self,
        signal: SemanticSignal,
        narrative_role: NarrativeRole,
        design_context: DesignContext | None = None,
        deck_budget: DeckVisualBudget | None = None,
    ) -> list[CandidateScore]:
        """Score all candidate VisualTypes and return deterministically sorted list."""
        scores: list[CandidateScore] = []

        for vtype, descriptor in ARCHETYPE_MAPPINGS.items():
            if vtype in (VisualType.NONE, VisualType.IMAGE, VisualType.ICON_GROUP):
                continue

            # Determine specific archetype name
            if vtype == VisualType.CARD_GRID:
                archetype_name = resolve_card_grid_archetype(signal.detected_entity_count)
            else:
                archetype_name = descriptor.preferred_archetype

            # 1. Semantic Match Score
            aff_cat = VISUAL_CATEGORY_AFFINITY.get(vtype, SemanticCategory.CATEGORICAL)
            sem_score = signal.category_scores.get(aff_cat, 0.0)

            # 2. Narrative Role Score
            role_score = 1.5 if vtype in ROLE_BONUSES.get(narrative_role, []) else 0.0

            # 3. Data Compatibility & Anti-Hallucination
            data_score = 0.0
            penalties = 0.0
            rationale_parts: list[str] = []

            if descriptor.requires_quantitative_data:
                if signal.has_quantitative_data:
                    data_score += 2.5
                    rationale_parts.append("Has required quantitative figures.")
                else:
                    # STRICT ANTI-HALLUCINATION: Heavy penalty if chart/KPI has no data
                    penalties += 8.0
                    rationale_parts.append("PENALTY: Lacks quantitative data.")

            # Specialized chart rules
            if vtype == VisualType.LINE_CHART:
                if signal.has_explicit_dates and signal.has_quantitative_data:
                    data_score += 3.5
                    rationale_parts.append("Continuous time trend with numeric metrics.")
                elif not signal.has_explicit_dates:
                    penalties += 3.0
                    rationale_parts.append("PENALTY: Line chart requires chronological series.")

            elif vtype in (VisualType.COLUMN_CHART, VisualType.BAR_CHART):
                if signal.has_quantitative_data and signal.primary_category not in (SemanticCategory.COMPARATIVE, SemanticCategory.TABULAR):
                    data_score += 2.0
                    rationale_parts.append("Discrete category metrics available.")
                elif signal.has_quantitative_data:
                    data_score += 0.5

            elif vtype in (VisualType.PIE_CHART, VisualType.DONUT_CHART):
                # Strict: Pie charts only for part-to-whole with <= 6 items
                if signal.has_quantitative_data and signal.detected_entity_count <= 6 and signal.primary_category not in (SemanticCategory.COMPARATIVE, SemanticCategory.TABULAR):
                    data_score += 1.0
                else:
                    penalties += 4.0

            elif vtype == VisualType.TIMELINE:
                if signal.has_explicit_dates:
                    data_score += 3.5
                    rationale_parts.append("Explicit milestone dates detected.")
                elif signal.has_sequential_steps:
                    data_score += 1.0

            elif vtype == VisualType.PROCESS_FLOW:
                if signal.has_sequential_steps:
                    data_score += 3.5
                    rationale_parts.append("Sequential workflow steps detected.")

            elif vtype == VisualType.COMPARISON:
                if signal.has_entity_comparison or signal.primary_category == SemanticCategory.COMPARATIVE:
                    data_score += 4.5
                    rationale_parts.append("Side-by-side comparison detected.")

            elif vtype == VisualType.ARCHITECTURE:
                if signal.has_system_components:
                    data_score += 4.5
                    rationale_parts.append("Multi-tier system architecture detected.")

            elif vtype == VisualType.HIERARCHY:
                if signal.primary_category == SemanticCategory.HIERARCHICAL:
                    data_score += 4.0
                    rationale_parts.append("Parent-child hierarchical structure detected.")

            elif vtype == VisualType.TABLE:
                if signal.primary_category in (SemanticCategory.TABULAR, SemanticCategory.COMPARATIVE):
                    data_score += 4.5
                    rationale_parts.append("Tabular specifications or comparison matrix detected.")

            elif vtype == VisualType.MATRIX:
                if signal.primary_category in (SemanticCategory.TABULAR, SemanticCategory.COMPARATIVE):
                    data_score += 4.0
                    rationale_parts.append("Multi-dimensional matrix structure detected.")

            elif vtype == VisualType.QUOTE:
                if signal.primary_category == SemanticCategory.KEY_STATEMENT:
                    data_score += 3.0
                    rationale_parts.append("Quotation / mission declaration detected.")

            # 4. Reference PPT Motif Bonus (Modest bonus, cannot override semantic correctness)
            ref_bonus = 0.0
            if design_context and design_context.archetype_hints:
                if archetype_name in design_context.archetype_hints or vtype.value in design_context.archetype_hints:
                    ref_bonus = 0.75
                    rationale_parts.append("Bonus from reference PPT design motif.")

            # 5. Visual Budget Repetition Penalty
            rep_penalty = 0.0
            if deck_budget:
                rep_penalty = deck_budget.get_repetition_penalty(archetype_name)
                if rep_penalty > 0:
                    penalties += rep_penalty
                    rationale_parts.append(f"Visual budget repetition penalty: -{rep_penalty:.2f}")

            # 6. Total Score Calculation
            total = max(0.0, round(sem_score + role_score + data_score + ref_bonus - penalties, 2))

            scores.append(
                CandidateScore(
                    visual_type=vtype,
                    archetype=archetype_name,
                    total_score=total,
                    semantic_match_score=sem_score,
                    narrative_role_score=role_score,
                    data_compatibility_score=data_score,
                    reference_bonus=ref_bonus,
                    penalties=penalties,
                    rationale="; ".join(rationale_parts) if rationale_parts else "Default categorical candidate.",
                )
            )

        # Deterministic sorting: highest score first; ties broken by visual_type name
        return sorted(scores, key=lambda c: (-c.total_score, c.visual_type.value))
