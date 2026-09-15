"""Domain models and data structures for Semantic Visual Selection Intelligence."""

from collections import Counter
from enum import Enum
from pydantic import BaseModel, Field

from backend.app.domain.enums import VisualType


class SemanticCategory(str, Enum):
    """Semantic category classifying the primary informational nature of slide content."""

    TEMPORAL = "temporal"            # Milestones, history, timeline, dates, roadmap
    SEQUENTIAL = "sequential"        # Step-by-step workflows, procedures, pipelines
    HIERARCHICAL = "hierarchical"    # Parent-child trees, reporting structures, multi-tier levels
    COMPARATIVE = "comparative"      # vs, pros/cons, option A vs B, side-by-side
    QUANTITATIVE = "quantitative"    # Numeric metrics, revenue, rates, percentages, growth stats
    RELATIONAL = "relational"        # Architecture, system components, microservices, data flow
    TABULAR = "tabular"              # Multi-attribute records, feature comparison matrices, specifications
    KEY_STATEMENT = "key_statement"  # Quotations, mission statements, big vision declarations
    CATEGORICAL = "categorical"      # Distinct independent buckets, concepts, feature cards
    PROSE = "prose"                  # Descriptive narrative without distinct visual structure


class SemanticSignal(BaseModel):
    """Extracted semantic signals and evidence from slide content."""

    primary_category: SemanticCategory = Field(default=SemanticCategory.CATEGORICAL)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    category_scores: dict[SemanticCategory, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    has_quantitative_data: bool = Field(default=False)
    has_explicit_dates: bool = Field(default=False)
    has_sequential_steps: bool = Field(default=False)
    has_entity_comparison: bool = Field(default=False)
    has_system_components: bool = Field(default=False)
    detected_entity_count: int = Field(default=0, ge=0)


class CandidateScore(BaseModel):
    """Scoring evaluation for a candidate visual archetype."""

    visual_type: VisualType
    archetype: str
    total_score: float
    semantic_match_score: float = 0.0
    narrative_role_score: float = 0.0
    data_compatibility_score: float = 0.0
    reference_bonus: float = 0.0
    penalties: float = 0.0
    rationale: str = ""


class SemanticVisualDecision(BaseModel):
    """Final deterministic visual selection decision for a single slide."""

    selected_visual_type: VisualType
    selected_archetype: str
    rationale: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    requires_quantitative_data: bool = False
    is_illustrative_data_allowed: bool = False
    fallback_visual_type: VisualType = VisualType.CARD_GRID
    fallback_archetype: str = "three_card_row"
    candidate_rankings: list[CandidateScore] = Field(default_factory=list)


class DeckVisualBudget:
    """Tracks and enforces slide-level and deck-level visual diversity budgets."""

    def __init__(self, max_consecutive_same_archetype: int = 2) -> None:
        self.max_consecutive = max_consecutive_same_archetype
        self.archetype_history: list[str] = []
        self.visual_type_history: list[VisualType] = []
        self.archetype_counts: Counter[str] = Counter()

    @property
    def last_archetype(self) -> str | None:
        return self.archetype_history[-1] if self.archetype_history else None

    @property
    def consecutive_same_count(self) -> int:
        if not self.archetype_history:
            return 0
        current = self.archetype_history[-1]
        count = 0
        for arch in reversed(self.archetype_history):
            if arch == current:
                count += 1
            else:
                break
        return count

    def get_repetition_penalty(self, archetype: str) -> float:
        """Calculate penalty if selecting this archetype would cause excessive repetition."""
        if not self.archetype_history:
            return 0.0

        if archetype == self.last_archetype:
            # If it would exceed max consecutive, apply heavy penalty
            if self.consecutive_same_count >= self.max_consecutive:
                return 0.65
            return 0.25

        # If archetype is heavily overused across the deck (>35% of total slides so far)
        total = len(self.archetype_history)
        if total >= 4:
            usage_ratio = self.archetype_counts[archetype] / total
            if usage_ratio > 0.40:
                return 0.30

        return 0.0

    def record_selection(self, visual_type: VisualType, archetype: str) -> None:
        """Record the selected visual archetype in history."""
        self.archetype_history.append(archetype)
        self.visual_type_history.append(visual_type)
        self.archetype_counts[archetype] += 1
