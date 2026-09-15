"""Unit tests for FakeAIProvider."""

import pytest
from backend.app.ai.context import DesignContext, PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.domain.constants import CURRENT_SCHEMA_VERSION
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.enums import NarrativeRole, VisualType
from backend.app.domain.presentation import Presentation


@pytest.mark.asyncio
async def test_fake_provider_generates_valid_presentation():
    provider = FakeAIProvider()
    req = PresentationGenerationRequest(
        topic="Cloud Infrastructure Engineering",
        slide_count=5,
        audience="Senior Engineers",
        purpose="System Architecture Review",
        style="modern_dark",
    )
    presentation = await provider.generate_presentation(req)

    assert isinstance(presentation, Presentation)
    assert presentation.schema_version == CURRENT_SCHEMA_VERSION
    assert presentation.metadata.title == "Cloud Infrastructure Engineering"
    assert presentation.metadata.slide_count == 5
    assert len(presentation.slides) == 5
    assert presentation.slides[0].narrative_role == NarrativeRole.TITLE
    assert presentation.slides[-1].narrative_role == NarrativeRole.CONCLUSION
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_fake_provider_respects_custom_design_context():
    provider = FakeAIProvider()
    custom_design = DesignSystem()
    custom_design.palette.primary = "#00FF66"

    req = PresentationGenerationRequest(
        mode="reference",
        topic="Green Energy Transition",
        slide_count=4,
        design_context=DesignContext(
            design_system=custom_design,
            style_name="Emerald Horizon",
        ),
    )
    presentation = await provider.generate_presentation(req)

    assert presentation.design_system.palette.primary == "#00FF66"
    assert presentation.metadata.slide_count == 4


@pytest.mark.asyncio
async def test_fake_provider_visual_diversity():
    provider = FakeAIProvider()
    req = PresentationGenerationRequest(
        topic="Enterprise Scaling Blueprint",
        slide_count=8,
    )
    presentation = await provider.generate_presentation(req)

    visual_types = [slide.visual_plan.visual_type for slide in presentation.slides]
    # Ensure visual variety across slides
    assert VisualType.PROCESS_FLOW in visual_types
    assert VisualType.KPI in visual_types
    assert VisualType.TIMELINE in visual_types
    assert VisualType.CARD_GRID in visual_types


@pytest.mark.asyncio
async def test_fake_provider_simulated_failures():
    # Timeout
    timeout_provider = FakeAIProvider(simulate_timeout=True)
    with pytest.raises(AIProviderTimeoutError):
        await timeout_provider.generate_presentation(
            PresentationGenerationRequest(topic="Timeout Test")
        )

    # Rate limit
    rate_limit_provider = FakeAIProvider(simulate_rate_limit=True)
    with pytest.raises(AIProviderRateLimitError):
        await rate_limit_provider.generate_presentation(
            PresentationGenerationRequest(topic="Rate Limit Test")
        )

    # General provider error
    error_provider = FakeAIProvider(simulate_error=True)
    with pytest.raises(AIProviderError):
        await error_provider.generate_presentation(
            PresentationGenerationRequest(topic="General Error Test")
        )

    # Invalid output
    invalid_provider = FakeAIProvider(simulate_invalid_output=True)
    with pytest.raises(AIOutputValidationError):
        await invalid_provider.generate_presentation(
            PresentationGenerationRequest(topic="Invalid Output Test")
        )
