"""Integration tests: End-to-end pipeline Phase 8 -> Phase 6 -> Phase 9 -> Phase 5 Native PPTX."""

import io
import zipfile
import pytest

from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.content import CardContent, KPIContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import (
    ElementType,
    NarrativeRole,
    ProcessDirection,
    TimelineStatus,
    VisualType,
)
from backend.app.domain.presentation import (
    Presentation,
    PresentationMetadata,
    Slide,
)
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
)
from backend.app.layout.engine import resolve_presentation_layout
from backend.app.rendering.engine import PPTXRenderer
from backend.app.visual_intelligence.selector import select_presentation_visuals
from backend.app.visual_qa.orchestrator import validate_and_correct_presentation


@pytest.fixture
def enterprise_multislide_deck() -> Presentation:
    """Multi-slide enterprise presentation fixture covering multiple archetypes."""
    slides = [
        # Slide 1: Cover / Title
        Slide(
            id="s1_cover",
            slide_number=1,
            title="NextGen Cloud Infrastructure",
            subtitle="Autonomous Microservices, Kubernetes Orchestration & Edge Mesh",
            narrative_role=NarrativeRole.TITLE,
            visual_plan=VisualPlan(visual_type=VisualType.HERO),
            elements=[
                Element(id="s1_t", type=ElementType.TEXT, role="title", text_content=TextContent(text="NextGen Cloud Infrastructure")),
                Element(id="s1_st", type=ElementType.TEXT, role="subtitle", text_content=TextContent(text="Autonomous Microservices, Kubernetes Orchestration & Edge Mesh")),
            ],
        ),
        # Slide 2: KPI Metrics
        Slide(
            id="s2_kpi",
            slide_number=2,
            title="Key Operational Metrics",
            subtitle="Global latency and throughput milestones",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(visual_type=VisualType.KPI),
            elements=[
                Element(id="s2_k1", type=ElementType.KPI, kpi_content=KPIContent(value="99.999%", label="Edge Availability", trend="up")),
                Element(id="s2_k2", type=ElementType.KPI, kpi_content=KPIContent(value="<5ms", label="P99 Global TTFB", trend="up")),
                Element(id="s2_k3", type=ElementType.KPI, kpi_content=KPIContent(value="10M+", label="RPS Handled", trend="up")),
            ],
        ),
        # Slide 3: Process Flow
        Slide(
            id="s3_proc",
            slide_number=3,
            title="CI/CD Automated Deployment Pipeline",
            subtitle="From git commit to multi-region zero-downtime rollout",
            narrative_role=NarrativeRole.PROCESS,
            visual_plan=VisualPlan(
                visual_type=VisualType.PROCESS_FLOW,
                process_flow_data=ProcessFlowData(
                    direction=ProcessDirection.HORIZONTAL,
                    steps=[
                        ProcessStep(id="st1", title="Code Commit", description="Triggers webhook", order=1),
                        ProcessStep(id="st2", title="Security Scan", description="SAST & DAST analysis", order=2),
                        ProcessStep(id="st3", title="Canary Deploy", description="1% traffic routing", order=3),
                        ProcessStep(id="st4", title="Global Promotion", description="100% live rollout", order=4),
                    ],
                ),
            ),
        ),
        # Slide 4: Timeline
        Slide(
            id="s4_time",
            slide_number=4,
            title="Cloud Transformation Roadmap",
            subtitle="Multi-year milestone progression",
            narrative_role=NarrativeRole.TIMELINE,
            visual_plan=VisualPlan(
                visual_type=VisualType.TIMELINE,
                timeline_data=TimelineData(
                    milestones=[
                        TimelineMilestone(label="Phase 1: Lift & Shift", date="Q1 2026", status=TimelineStatus.COMPLETED),
                        TimelineMilestone(label="Phase 2: Microservices", date="Q3 2026", status=TimelineStatus.CURRENT),
                        TimelineMilestone(label="Phase 3: Multi-Cloud", date="Q2 2027", status=TimelineStatus.PLANNED),
                    ]
                ),
            ),
        ),
        # Slide 5: Comparison
        Slide(
            id="s5_comp",
            slide_number=5,
            title="Monolithic vs Serverless Mesh",
            subtitle="Architectural tradeoffs and scaling characteristics",
            narrative_role=NarrativeRole.COMPARISON,
            visual_plan=VisualPlan(visual_type=VisualType.COMPARISON),
            elements=[
                Element(id="c_left", type=ElementType.CARD, card_content=CardContent(title="Monolithic Architecture", body="Single deployable artifact, tight coupling, manual scaling")),
                Element(id="c_right", type=ElementType.CARD, card_content=CardContent(title="Serverless Edge Mesh", body="Event-driven auto-scaling, isolated failure domains, zero idle costs")),
            ],
        ),
        # Slide 6: Table
        Slide(
            id="s6_tbl",
            slide_number=6,
            title="Tier SLA Comparison Matrix",
            subtitle="Service level agreements across customer tiers",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(
                visual_type=VisualType.TABLE,
                table_data=TableData(
                    columns=[
                        TableColumn(key="tier", label="Tier"),
                        TableColumn(key="avail", label="Availability"),
                        TableColumn(key="support", label="Support"),
                        TableColumn(key="credit", label="SLA Credit"),
                    ],
                    rows=[
                        TableRow(cells=["Developer", "99.9%", "Community", "10%"]),
                        TableRow(cells=["Business", "99.99%", "24/7 Email", "25%"]),
                        TableRow(cells=["Enterprise", "99.999%", "Dedicated TAM", "50%"]),
                    ],
                ),
            ),
        ),
        # Slide 7: Chart
        Slide(
            id="s7_chart",
            slide_number=7,
            title="Quarterly Cloud Cost Reductions",
            subtitle="Year-over-year infrastructure savings in millions USD",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(
                visual_type=VisualType.BAR_CHART,
                chart_data=ChartData(
                    title="Cost Savings ($M)",
                    categories=["Q1", "Q2", "Q3", "Q4"],
                    series=[ChartSeries(name="Savings", values=[1.2, 2.5, 4.1, 6.8])],
                ),
            ),
        ),
    ]

    return Presentation(
        metadata=PresentationMetadata(
            title="NextGen Cloud Infrastructure",
            topic="Cloud Modernization",
            slide_count=7,
        ),
        design_system=DesignSystem(),
        slides=slides,
    )


def test_full_pipeline_phase_8_to_6_to_9_to_5(enterprise_multislide_deck: Presentation) -> None:
    """Execute complete end-to-end pipeline:
    Phase 8 Visual Selection -> Phase 6 Layout -> Phase 9 Visual QA & Auto-Correction -> Phase 5 Native PPTX.
    """
    # 1. Phase 8: Refine Visual Selection
    refined_presentation = select_presentation_visuals(enterprise_multislide_deck)
    assert len(refined_presentation.slides) == 7

    # 2. Phase 6: Initial Deterministic Layout
    raw_layout = resolve_presentation_layout(refined_presentation)
    assert len(raw_layout.slides) == 7

    # 3. Phase 9: Visual QA & 3-Pass Auto-Correction
    qa_result = validate_and_correct_presentation(refined_presentation, raw_layout)
    assert qa_result.passed is True
    assert qa_result.final_quality_score >= 80.0
    assert qa_result.critical_issues == 0
    assert qa_result.errors == 0
    assert qa_result.layout is not None

    # 4. Phase 5: Native PPTX Rendering
    renderer = PPTXRenderer()
    pptx_bytes = renderer.render_to_bytes(refined_presentation, qa_result)
    assert len(pptx_bytes) > 5000

    # 5. Verify OpenXML / ZIP package validity
    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "[Content_Types].xml" in namelist
        assert "ppt/presentation.xml" in namelist
        # Check all 7 slides are rendered as separate XML slide parts
        for i in range(1, 8):
            assert f"ppt/slides/slide{i}.xml" in namelist
