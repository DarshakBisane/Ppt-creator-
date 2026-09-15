"""Semantic Visual Selection Intelligence module."""

from backend.app.visual_intelligence.archetype_map import (
    ARCHETYPE_MAPPINGS,
    ArchetypeDescriptor,
    get_archetype_descriptor,
)
from backend.app.visual_intelligence.classifier import ContentSemanticClassifier
from backend.app.visual_intelligence.exceptions import (
    IncompatibleVisualDataError,
    VisualIntelligenceError,
    VisualSelectionError,
)
from backend.app.visual_intelligence.models import (
    CandidateScore,
    DeckVisualBudget,
    SemanticCategory,
    SemanticSignal,
    SemanticVisualDecision,
)
from backend.app.visual_intelligence.rules import VisualScoringEngine
from backend.app.visual_intelligence.selector import (
    SemanticVisualSelector,
    default_visual_selector,
    select_presentation_visuals,
)

__all__ = [
    "ARCHETYPE_MAPPINGS",
    "ArchetypeDescriptor",
    "CandidateScore",
    "ContentSemanticClassifier",
    "DeckVisualBudget",
    "IncompatibleVisualDataError",
    "SemanticCategory",
    "SemanticSignal",
    "SemanticVisualDecision",
    "SemanticVisualSelector",
    "VisualIntelligenceError",
    "VisualScoringEngine",
    "VisualSelectionError",
    "default_visual_selector",
    "get_archetype_descriptor",
    "select_presentation_visuals",
]
