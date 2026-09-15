"""End-to-end Mode B integration tests connecting Reference PPT Analyzer with AI and Layout engines."""

import io
import zipfile
import pytest

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.ai.prompts import PromptBuilder
from backend.app.layout.engine import LayoutEngine
from backend.app.reference.analyzer import ReferencePPTAnalyzer
from backend.app.rendering.engine import PPTXRenderer


def test_reference_mode_b_end_to_end_pipeline(dark_theme_pptx_bytes: bytes) -> None:
    """Verify Mode B workflow: Reference PPTX -> DesignContext -> Request -> Presentation -> Layout -> PPTX."""
    # 1. Analyze Reference Deck
    analyzer = ReferencePPTAnalyzer()
    design_context, design_system, summary = analyzer.analyze(dark_theme_pptx_bytes)

    assert design_context is not None
    assert summary.is_dark_mode is True

    # 2. Build Generation Request with extracted DesignContext
    request = PresentationGenerationRequest(
        mode="reference",
        topic="Scalable Microservices on Kubernetes",
        slide_count=6,
        audience="Principal Architects",
        purpose="Engineering Deep-Dive",
        design_context=design_context,
    )

    # 3. Verify PromptBuilder embeds quarantined design tokens safely
    user_prompt = PromptBuilder.build_user_prompt(request)
    assert "<reference_untrusted_data>" in user_prompt
    assert "</reference_untrusted_data>" in user_prompt
    assert "Design Palette Tokens:" in user_prompt

    # 4. Generate Presentation domain model using FakeAIProvider
    presentation = FakeAIProvider.create_deterministic_presentation(request)
    # Apply the extracted design system to the presentation
    presentation.design_system = design_system

    # 5. Resolve layout with deterministic layout engine
    layout_engine = LayoutEngine()
    layout_result = layout_engine.layout_presentation(presentation)
    assert len(layout_result.slides) == 6

    # 6. Render to native PPTX
    renderer = PPTXRenderer()
    out_bytes = renderer.render_to_bytes(presentation, layout_result)
    assert len(out_bytes) > 0

    # 7. Validate generated OpenXML package
    with zipfile.ZipFile(io.BytesIO(out_bytes), "r") as zf:
        file_list = zf.namelist()
        assert "[Content_Types].xml" in file_list
        assert "ppt/presentation.xml" in file_list
        assert len([f for f in file_list if f.startswith("ppt/slides/slide")]) == 6
