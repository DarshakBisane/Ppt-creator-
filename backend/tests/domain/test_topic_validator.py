"""Tests for SemanticTopicValidator and topic boundary enforcement."""

import pytest
from backend.app.domain.content import CardContent, TextContent
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.presentation_intelligence.topic_validator import SemanticTopicValidator


def test_topic_validator_detects_leakage() -> None:
    """Test that generator stack terms are flagged as leakage on non-generator topics."""
    topic = "X.509 Digital Certificate Management System"
    assert SemanticTopicValidator.is_generator_leakage("FastAPI backend layer", topic) is True
    assert SemanticTopicValidator.is_generator_leakage("React 19 Interactive Client UI", topic) is True
    assert SemanticTopicValidator.is_generator_leakage("Deterministic 1920x1080 constraint solver", topic) is True
    assert SemanticTopicValidator.is_generator_leakage("python-pptx rendering pipeline", topic) is True
    assert SemanticTopicValidator.is_generator_leakage("PresenAI correlation ID engine", topic) is True


def test_topic_validator_allows_legitimate_terms_when_requested() -> None:
    """Test that terms requested explicitly by the user are not falsely blocked."""
    topic = "Building High-Performance APIs with FastAPI and Python"
    assert SemanticTopicValidator.is_generator_leakage("FastAPI route handler and Pydantic models", topic) is False


def test_topic_validator_disinfects_presentation() -> None:
    """Test that sanitize_presentation replaces leaked phrases with clean domain content."""
    topic = "X.509 Digital Certificate Management System"
    slide = Slide(
        id="s_arch",
        slide_number=1,
        title="System Architecture",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.ARCHITECTURE),
        elements=[
            Element(
                id="e1",
                type=ElementType.CARD,
                card_content=CardContent(
                    title="React 19 UI & Vite Pipeline",
                    body="Deterministic 1920x1080 constraint solver and python-pptx engine",
                ),
            ),
        ],
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="X.509 System", topic=topic, slide_count=1),
        slides=[slide],
    )

    cleaned, sanitizations = SemanticTopicValidator.sanitize_presentation(pres)
    assert sanitizations >= 2
    assert "React 19" not in cleaned.slides[0].elements[0].card_content.title
    assert "1920x1080" not in cleaned.slides[0].elements[0].card_content.body
    assert "python-pptx" not in cleaned.slides[0].elements[0].card_content.body
