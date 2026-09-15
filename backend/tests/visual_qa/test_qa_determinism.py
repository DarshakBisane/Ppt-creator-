"""Unit tests verifying strict determinism of the Visual QA & Auto-Correction pipeline."""

from backend.app.domain.content import CardContent, KPIContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.visuals import VisualPlan
from backend.app.visual_qa.orchestrator import validate_and_correct_presentation


def test_visual_qa_pipeline_determinism() -> None:
    """Running Visual QA and auto-correction on identical input produces identical output."""
    slides = [
        Slide(
            id="s1",
            slide_number=1,
            title="Strategic Architecture",
            narrative_role=NarrativeRole.ARCHITECTURE,
            visual_plan=VisualPlan(visual_type=VisualType.ARCHITECTURE),
            elements=[
                Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="API Gateway", body="Ingress routing")),
                Element(id="c2", type=ElementType.CARD, card_content=CardContent(title="Core Auth", body="JWT validation")),
                Element(id="c3", type=ElementType.CARD, card_content=CardContent(title="Data Tier", body="PostgreSQL replica")),
            ],
        ),
        Slide(
            id="s2",
            slide_number=2,
            title="Performance Metrics",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(visual_type=VisualType.KPI),
            elements=[
                Element(id="k1", type=ElementType.KPI, kpi_content=KPIContent(value="99.99%", label="Uptime SLA")),
                Element(id="k2", type=ElementType.KPI, kpi_content=KPIContent(value="15ms", label="P99 Latency")),
            ],
        ),
    ]

    presentation = Presentation(
        metadata=PresentationMetadata(title="Deterministic Benchmark", topic="Tech Architecture", slide_count=2),
        design_system=DesignSystem(),
        slides=slides,
    )

    run_1 = validate_and_correct_presentation(presentation)
    run_2 = validate_and_correct_presentation(presentation)

    # 1. Status and scores must match exactly
    assert run_1.passed == run_2.passed
    assert run_1.final_status == run_2.final_status
    assert run_1.final_quality_score == run_2.final_quality_score
    assert run_1.total_issues == run_2.total_issues
    assert len(run_1.corrections_applied) == len(run_2.corrections_applied)

    # 2. Geometric coordinates must match exactly
    assert run_1.layout is not None and run_2.layout is not None
    for s1, s2 in zip(run_1.layout.slides, run_2.layout.slides):
        assert len(s1.elements) == len(s2.elements)
        for e1, e2 in zip(s1.elements, s2.elements):
            assert e1.id == e2.id
            assert e1.rect == e2.rect
            assert e1.ports == e2.ports
