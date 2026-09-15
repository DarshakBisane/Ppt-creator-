"""Integration test: End-to-end presentation layout and native PPTX generation."""

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
from backend.app.layout.engine import LayoutEngine
from backend.app.rendering.engine import PPTXRenderer


@pytest.fixture
def banking_presentation_fixture() -> Presentation:
    """Realistic enterprise presentation fixture on 'AI in Modern Banking'."""
    slides: list[Slide] = [
        # Slide 1: Title
        Slide(
            id="s1_cover",
            slide_number=1,
            title="AI in Modern Banking",
            subtitle="Autonomous Intelligence, Fraud Defense & Algorithmic Underwriting",
            narrative_role=NarrativeRole.TITLE,
            purpose="Executive Briefing & Strategic Technology Outlook",
            visual_plan=VisualPlan(visual_type=VisualType.NONE),
            elements=[
                Element(id="s1_e1", type=ElementType.TEXT, role="title", text_content=TextContent(text="AI in Modern Banking")),
                Element(id="s1_e2", type=ElementType.TEXT, role="subtitle", text_content=TextContent(text="Executive Briefing & Strategic Technology Outlook")),
            ],
            speaker_notes="Welcome board members. Today we present our multi-year AI transformation strategy for retail and commercial banking.",
        ),
        # Slide 2: KPI Dashboard
        Slide(
            id="s2_kpi",
            slide_number=2,
            title="Strategic Financial & Operational Impact",
            subtitle="Measurable acceleration across digital channels",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(visual_type=VisualType.KPI),
            elements=[
                Element(id="s2_k1", type=ElementType.KPI, kpi_content=KPIContent(value="$420M", label="Annual Fraud Prevention", trend="up", context="42% reduction in false positives")),
                Element(id="s2_k2", type=ElementType.KPI, kpi_content=KPIContent(value="<120ms", label="Real-Time Credit Decisioning", trend="up", context="Sub-second algorithmic approval")),
                Element(id="s2_k3", type=ElementType.KPI, kpi_content=KPIContent(value="94.6%", label="Customer STP Rate", trend="up", context="Straight-through processing")),
            ],
            speaker_notes="Our machine learning models have prevented over $420M in unauthorized transactions while reducing underwriting latency to under 120 milliseconds.",
        ),
        # Slide 3: Three Pillars (Cards)
        Slide(
            id="s3_pillars",
            slide_number=3,
            title="Core Banking Intelligence Pillars",
            subtitle="Foundations for resilient AI deployment",
            narrative_role=NarrativeRole.SOLUTION,
            visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
            elements=[
                Element(id="s3_c1", type=ElementType.CARD, card_content=CardContent(title="Autonomous Fraud Defense", body="Graph neural networks analyzing 50,000 transactions per second in real time.")),
                Element(id="s3_c2", type=ElementType.CARD, card_content=CardContent(title="Conversational Wealth Advisor", body="Hyper-personalized portfolio insights driven by fine-tuned financial LLMs.")),
                Element(id="s3_c3", type=ElementType.CARD, card_content=CardContent(title="Automated Regulatory Audit", body="Continuous compliance monitoring ensuring zero-drift adherence to global mandates.")),
            ],
        ),
        # Slide 4: Comparison
        Slide(
            id="s4_compare",
            slide_number=4,
            title="Legacy vs. AI-Native Core Banking",
            subtitle="Architectural evolution of transaction pipelines",
            narrative_role=NarrativeRole.COMPARISON,
            visual_plan=VisualPlan(visual_type=VisualType.COMPARISON),
        ),
        # Slide 5: Process Flow
        Slide(
            id="s5_process",
            slide_number=5,
            title="Real-Time Loan Origination Pipeline",
            subtitle="End-to-end deterministic processing sequence",
            narrative_role=NarrativeRole.PROCESS,
            visual_plan=VisualPlan(
                visual_type=VisualType.PROCESS_FLOW,
                process_flow_data=ProcessFlowData(
                    direction=ProcessDirection.HORIZONTAL,
                    steps=[
                        ProcessStep(id="ps1", title="Identity & KYC Verification", description="Biometric authentication and anti-spoofing verification.", order=1),
                        ProcessStep(id="ps2", title="Alternative Credit Scoring", description="Ingestion of cash-flow and telemetry data signals.", order=2),
                        ProcessStep(id="ps3", title="Automated Risk Pricing", description="Dynamic interest rate calculation and risk tiering.", order=3),
                        ProcessStep(id="ps4", title="Instant Disbursal", description="Zero-touch settlement via instant payment rails.", order=4),
                    ],
                ),
            ),
        ),
        # Slide 6: Timeline
        Slide(
            id="s6_timeline",
            slide_number=6,
            title="Enterprise Rollout Roadmap",
            subtitle="Multi-phase production implementation schedule",
            narrative_role=NarrativeRole.TIMELINE,
            visual_plan=VisualPlan(
                visual_type=VisualType.TIMELINE,
                timeline_data=TimelineData(
                    title="Rollout Schedule",
                    milestones=[
                        TimelineMilestone(label="Phase 1", date="Q1 2026", description="Core Fraud Model Deployment", status=TimelineStatus.COMPLETED),
                        TimelineMilestone(label="Phase 2", date="Q2 2026", description="Underwriting Engine Migration", status=TimelineStatus.CURRENT),
                        TimelineMilestone(label="Phase 3", date="Q3 2026", description="Autonomous Assistant Rollout", status=TimelineStatus.PLANNED),
                        TimelineMilestone(label="Phase 4", date="Q4 2026", description="Global Multi-Region GA", status=TimelineStatus.PLANNED),
                    ],
                ),
            ),
        ),
        # Slide 7: Architecture
        Slide(
            id="s7_arch",
            slide_number=7,
            title="Banking Intelligence Architecture",
            subtitle="Tiered microservices and data stream topology",
            narrative_role=NarrativeRole.ARCHITECTURE,
            visual_plan=VisualPlan(visual_type=VisualType.ARCHITECTURE),
        ),
        # Slide 8: Native Table
        Slide(
            id="s8_table",
            slide_number=8,
            title="Operational Benchmark Matrix",
            subtitle="Performance comparison across banking tiers",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(
                visual_type=VisualType.TABLE,
                table_data=TableData(
                    columns=[
                        TableColumn(key="metric", label="Key Metric"),
                        TableColumn(key="legacy", label="Legacy Core"),
                        TableColumn(key="presen_ai", label="AI-Native Core"),
                        TableColumn(key="delta", label="Delta"),
                    ],
                    rows=[
                        TableRow(cells=["Loan Decisioning Time", "3 - 5 Days", "< 120 Milliseconds", "99.9% Faster"]),
                        TableRow(cells=["Fraud Detection Precision", "68.4%", "97.8%", "+29.4 pts"]),
                        TableRow(cells=["Cost Per Origination", "$240", "$18", "92.5% Reduction"]),
                    ],
                ),
            ),
        ),
        # Slide 9: Native Chart
        Slide(
            id="s9_chart",
            slide_number=9,
            title="Digital Banking Adoption & Cost Trajectory",
            subtitle="Projected annual operating expenditures ($ Millions)",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(
                visual_type=VisualType.COLUMN_CHART,
                chart_data=ChartData(
                    chart_type="column",
                    title="Operating Cost by Year ($M)",
                    categories=["2023", "2024", "2025", "2026 (Target)"],
                    series=[
                        ChartSeries(name="Legacy Run Cost", values=[120.0, 115.0, 110.0, 95.0]),
                        ChartSeries(name="AI-Native Run Cost", values=[25.0, 35.0, 48.0, 52.0]),
                    ],
                ),
            ),
        ),
    ]

    return Presentation(
        metadata=PresentationMetadata(
            title="AI in Modern Banking",
            topic="AI in Modern Banking",
            subtitle="Executive Briefing & Strategic Technology Outlook",
            audience="Executive Board & Technology Steering Committee",
            purpose="Strategic Technology Briefing",
            slide_count=9,
        ),
        design_system=DesignSystem(),
        slides=slides,
    )


def test_banking_presentation_integration_to_pptx(
    banking_presentation_fixture: Presentation,
) -> None:
    """Execute complete end-to-end pipeline: Presentation -> LayoutEngine -> PPTXRenderer -> Real Editable PPTX."""
    layout_engine = LayoutEngine()
    renderer = PPTXRenderer()

    # 1. Resolve deterministic presentation layout
    layout_result = layout_engine.layout_presentation(banking_presentation_fixture)
    assert len(layout_result.slides) == 9

    # 2. Render to PPTX binary bytes
    pptx_bytes = renderer.render_to_bytes(banking_presentation_fixture, layout_result)
    assert len(pptx_bytes) > 0

    # 3. Verify PPTX is a valid OpenXML ZIP package
    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        file_list = zf.namelist()

        # Check essential OpenXML files
        assert "[Content_Types].xml" in file_list
        assert "ppt/presentation.xml" in file_list

        # Check all 9 slide XMLs exist
        for i in range(1, 10):
            slide_xml_path = f"ppt/slides/slide{i}.xml"
            assert slide_xml_path in file_list, f"Missing {slide_xml_path} in generated PPTX package"

            # Read slide XML content to inspect native shapes and text
            slide_xml_content = zf.read(slide_xml_path).decode("utf-8")

            # Must contain native PowerPoint shapes (<p:sp>)
            assert "<p:sp" in slide_xml_content

            # Must contain native text runs (<a:t>)
            assert "<a:t>" in slide_xml_content or "<a:t " in slide_xml_content

        # Slide 8 should contain native PowerPoint table markup (<a:tbl>)
        slide8_xml = zf.read("ppt/slides/slide8.xml").decode("utf-8")
        assert "<a:tbl" in slide8_xml, "Slide 8 does not contain native PowerPoint table markup"

        # Check charts exist in OpenXML package
        chart_parts = [name for name in file_list if "ppt/charts/chart" in name]
        assert len(chart_parts) >= 1, "Generated PPTX does not contain native chart part"
