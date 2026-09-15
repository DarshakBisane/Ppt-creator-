"""Tests for ContentSemanticClassifier multi-signal extraction."""

from backend.app.domain.elements import CardContent, Element, KPIContent, TextContent
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Slide
from backend.app.visual_intelligence.classifier import ContentSemanticClassifier
from backend.app.visual_intelligence.models import SemanticCategory


def test_classify_temporal_slide(timeline_slide: Slide) -> None:
    classifier = ContentSemanticClassifier()
    signal = classifier.classify_slide(timeline_slide)

    assert signal.primary_category == SemanticCategory.TEMPORAL
    assert signal.has_explicit_dates is True
    assert signal.confidence >= 0.70


def test_classify_sequential_slide(process_slide: Slide) -> None:
    classifier = ContentSemanticClassifier()
    signal = classifier.classify_slide(process_slide)

    assert signal.primary_category == SemanticCategory.SEQUENTIAL
    assert signal.has_sequential_steps is True
    assert signal.confidence >= 0.70


def test_classify_comparative_slide(comparison_slide: Slide) -> None:
    classifier = ContentSemanticClassifier()
    signal = classifier.classify_slide(comparison_slide)

    assert signal.primary_category == SemanticCategory.COMPARATIVE
    assert signal.has_entity_comparison is True
    assert signal.confidence >= 0.70


def test_classify_quantitative_slide(quantitative_slide: Slide) -> None:
    classifier = ContentSemanticClassifier()
    signal = classifier.classify_slide(quantitative_slide)

    assert signal.primary_category == SemanticCategory.QUANTITATIVE
    assert signal.has_quantitative_data is True


def test_classify_architecture_slide(architecture_slide: Slide) -> None:
    classifier = ContentSemanticClassifier()
    signal = classifier.classify_slide(architecture_slide)

    assert signal.primary_category == SemanticCategory.RELATIONAL
    assert signal.has_system_components is True


def test_classify_quote_statement_slide(make_slide) -> None:
    classifier = ContentSemanticClassifier()
    slide = make_slide(
        title="Executive Vision & Core Mission Statement",
        narrative_role=NarrativeRole.TITLE,
        elements=[
            Element(
                id="q1",
                type=ElementType.TEXT,
                text_content=TextContent(text='"Our mission is to empower every developer on Earth with autonomous AI presentation tools." — CEO'),
            )
        ],
    )
    signal = classifier.classify_slide(slide)
    assert signal.primary_category == SemanticCategory.KEY_STATEMENT
