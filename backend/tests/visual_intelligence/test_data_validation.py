"""Tests for data validation, anti-hallucination guarantees, and chart eligibility."""

from backend.app.domain.elements import CardContent, Element, TextContent
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.visual_intelligence.classifier import ContentSemanticClassifier
from backend.app.visual_intelligence.rules import VisualScoringEngine
from backend.app.visual_intelligence.selector import SemanticVisualSelector


def test_no_quantitative_data_penalizes_charts_heavily(make_slide) -> None:
    """Prose without quantitative numbers must heavily penalize all chart types."""
    classifier = ContentSemanticClassifier()
    engine = VisualScoringEngine()

    slide = make_slide(
        title="Qualitative Strategic Vision & Future Principles",
        narrative_role=NarrativeRole.CONTEXT,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="First Pillar", body="Deep customer empathy")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Second Pillar", body="Continuous innovation")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Third Pillar", body="Operational rigor")),
        ],
    )
    signal = classifier.classify_slide(slide)
    candidates = engine.evaluate_candidates(signal, slide.narrative_role)

    # Charts should be at the bottom due to heavy missing data penalty
    top_vtypes = [c.visual_type for c in candidates[:3]]
    assert VisualType.LINE_CHART not in top_vtypes
    assert VisualType.COLUMN_CHART not in top_vtypes
    assert VisualType.PIE_CHART not in top_vtypes


def test_chart_candidate_fallback_when_series_missing(make_slide) -> None:
    """If a chart is manually set but lacks valid series data, it safely falls back."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Revenue Overview Without Numbers",
        narrative_role=NarrativeRole.EVIDENCE,
        elements=[
            Element(id="e1", type=ElementType.TEXT, text_content=TextContent(text="Growth was strong last quarter across all teams.")),
        ],
        visual_type=VisualType.LINE_CHART,
    )
    decision = selector.select_visual_for_slide(slide)

    # Must fall back gracefully to a non-chart visual or card grid
    assert decision.selected_visual_type in (VisualType.CARD_GRID, VisualType.TEXT, VisualType.HERO)
