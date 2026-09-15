import io
import zipfile
import pytest
from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.domain.presentation import Presentation
from backend.app.layout.engine import LayoutEngine
from backend.app.rendering.engine import PPTXRenderer
from backend.app.visual_intelligence.selector import SemanticVisualSelector


@pytest.mark.anyio
async def test_full_pipeline_process_presentation() -> None:
    """End-to-end generation for a Process presentation verifying native shapes & connectors."""
    provider = FakeAIProvider()
    req = PresentationGenerationRequest(
        topic="Modern Cloud Deployment and Continuous Delivery Workflow",
        slide_count=4,
    )
    presentation = await provider.generate_presentation(req)

    # Refine with Phase 8 Semantic Visual Selector
    selector = SemanticVisualSelector()
    refined = selector.refine_presentation(presentation)

    # Layout with Phase 6
    layout_engine = LayoutEngine()
    layout_result = layout_engine.layout_presentation(refined)

    # Render with Phase 5 PPTX Renderer
    renderer = PPTXRenderer()
    pptx_bytes = renderer.render_to_bytes(refined, layout_result)

    # Inspect OpenXML package
    zip_buf = io.BytesIO(pptx_bytes)
    with zipfile.ZipFile(zip_buf, "r") as z:
        names = z.namelist()
        assert "[Content_Types].xml" in names
        assert "ppt/presentation.xml" in names

        # Read slide XMLs and check for native shapes
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<p:sp" in slide_xml or "<p:cxnSp" in slide_xml


@pytest.mark.anyio
async def test_six_representative_visual_presentations() -> None:
    """Generate 6 representative presentations (Process, Timeline, Metrics, Architecture, Comparison, Roadmap)."""
    provider = FakeAIProvider()
    selector = SemanticVisualSelector()
    layout_engine = LayoutEngine()
    renderer = PPTXRenderer()

    test_topics = [
        "Modern CI/CD Engineering Pipeline Execution Steps",
        "Company Historical Evolution and Key Milestones 2020-2026",
        "Enterprise ARR Revenue Metrics and Financial KPI Dashboard",
        "Distributed Cloud Architecture & Microservices Infrastructure Stack",
        "Monolithic Architecture vs Event-Driven Microservices Comparison",
        "Enterprise Multi-Horizon Strategic Product Roadmap",
    ]

    for topic in test_topics:
        req = PresentationGenerationRequest(topic=topic, slide_count=4)
        raw_pres = await provider.generate_presentation(req)
        refined_pres = selector.refine_presentation(raw_pres)
        layout_res = layout_engine.layout_presentation(refined_pres)
        pptx_bytes = renderer.render_to_bytes(refined_pres, layout_res)

        assert len(pptx_bytes) > 5000

        # Verify valid ZIP package
        zip_buf = io.BytesIO(pptx_bytes)
        with zipfile.ZipFile(zip_buf, "r") as z:
            assert "ppt/presentation.xml" in z.namelist()
            assert len([f for f in z.namelist() if f.startswith("ppt/slides/slide")]) >= 4
