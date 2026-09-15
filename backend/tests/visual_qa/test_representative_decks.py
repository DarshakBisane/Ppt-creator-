"""Representative 10-archetype presentations test suite verifying native PPTX output and QA diagnostics."""

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
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
)
from backend.app.rendering.engine import PPTXRenderer
from backend.app.visual_intelligence.selector import select_presentation_visuals
from backend.app.visual_qa.orchestrator import validate_and_correct_presentation


def run_pipeline_and_verify_pptx(presentation: Presentation, expected_slides_count: int) -> bytes:
    """Helper to run Phase 8 -> Phase 6 -> Phase 9 -> Phase 5 and verify OpenXML structure."""
    # 1. Phase 8 Semantic Refinement
    refined = select_presentation_visuals(presentation)
    # 2. Phase 9 Visual QA & Auto-Correction
    qa_result = validate_and_correct_presentation(refined)
    assert qa_result.passed is True
    assert qa_result.final_quality_score >= 70.0
    assert qa_result.critical_issues == 0
    assert qa_result.errors == 0
    assert qa_result.layout is not None

    # 3. Phase 5 Native PPTX Rendering
    renderer = PPTXRenderer()
    pptx_bytes = renderer.render_to_bytes(refined, qa_result)
    assert len(pptx_bytes) > 4000

    # 4. OpenXML ZIP Verification
    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "[Content_Types].xml" in namelist
        assert "ppt/presentation.xml" in namelist
        for idx in range(1, expected_slides_count + 1):
            assert f"ppt/slides/slide{idx}.xml" in namelist

    return pptx_bytes


def test_deck_1_process() -> None:
    """Representative Deck 1: Process Flow."""
    slide = Slide(
        id="s_proc",
        slide_number=1,
        title="Payment Authorization Flow",
        subtitle="Step-by-step transaction validation sequence",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(
            visual_type=VisualType.PROCESS_FLOW,
            process_flow_data=ProcessFlowData(
                steps=[
                    ProcessStep(id="p1", title="Payment Token Created", description="App sends token to gateway", order=1),
                    ProcessStep(id="p2", title="Risk & Fraud Analysis", description="ML model scores transaction", order=2),
                    ProcessStep(id="p3", title="Acquiring Bank Capture", description="Funds captured from card network", order=3),
                ]
            ),
        ),
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Payment Pipeline", topic="Fintech Payments", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_2_timeline() -> None:
    """Representative Deck 2: Timeline."""
    slide = Slide(
        id="s_time",
        slide_number=1,
        title="Enterprise Migration Horizon",
        subtitle="Key milestone dates",
        narrative_role=NarrativeRole.TIMELINE,
        visual_plan=VisualPlan(
            visual_type=VisualType.TIMELINE,
            timeline_data=TimelineData(
                milestones=[
                    TimelineMilestone(label="Discovery & Audit", date="Jan 2026", status=TimelineStatus.COMPLETED),
                    TimelineMilestone(label="Pilot Kubernetes Cluster", date="May 2026", status=TimelineStatus.CURRENT),
                    TimelineMilestone(label="Full Cutover", date="Dec 2026", status=TimelineStatus.PLANNED),
                ]
            ),
        ),
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Migration Timeline", topic="Cloud Migration", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_3_metrics_kpi() -> None:
    """Representative Deck 3: Metrics / KPI Dashboard."""
    slide = Slide(
        id="s_kpi",
        slide_number=1,
        title="Executive Performance Scorecard",
        subtitle="Key operational benchmarks",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(visual_type=VisualType.KPI),
        elements=[
            Element(id="k1", type=ElementType.KPI, kpi_content=KPIContent(value="$85.2M", label="Annual Recurring Revenue", trend="up")),
            Element(id="k2", type=ElementType.KPI, kpi_content=KPIContent(value="142%", label="Net Revenue Retention", trend="up")),
            Element(id="k3", type=ElementType.KPI, kpi_content=KPIContent(value="18ms", label="Average API Latency", trend="down")),
        ],
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="KPI Scorecard", topic="Executive Metrics", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_4_architecture() -> None:
    """Representative Deck 4: Architecture Diagram."""
    slide = Slide(
        id="s_arch",
        slide_number=1,
        title="Distributed Event-Driven Architecture",
        subtitle="Multi-tier microservices topology",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.ARCHITECTURE),
        elements=[
            Element(id="a1", type=ElementType.CARD, card_content=CardContent(title="Client Edge", body="Next.js SSR + CDN")),
            Element(id="a2", type=ElementType.CARD, card_content=CardContent(title="API Gateway", body="Kong reverse proxy")),
            Element(id="a3", type=ElementType.CARD, card_content=CardContent(title="Service Mesh", body="Istio Envoy sidecars")),
        ],
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="System Architecture", topic="Cloud Topology", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_5_comparison() -> None:
    """Representative Deck 5: Comparison."""
    slide = Slide(
        id="s_comp",
        slide_number=1,
        title="Self-Hosted vs Managed SaaS",
        subtitle="Cost, operations, and maintenance comparison",
        narrative_role=NarrativeRole.COMPARISON,
        visual_plan=VisualPlan(visual_type=VisualType.COMPARISON),
        elements=[
            Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="Self-Hosted Cluster", body="Requires 3 FTE DevOps engineers, manual patching, infrastructure overhead")),
            Element(id="c2", type=ElementType.CARD, card_content=CardContent(title="Managed Cloud SaaS", body="Fully managed SLAs, automated zero-downtime upgrades, usage-based pricing")),
        ],
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Architecture Comparison", topic="Deployment Options", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_6_roadmap() -> None:
    """Representative Deck 6: Roadmap / Horizon."""
    slide = Slide(
        id="s_road",
        slide_number=1,
        title="Product Strategic Roadmap",
        subtitle="Three horizons of innovation",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(
            visual_type=VisualType.ROADMAP,
            timeline_data=TimelineData(
                milestones=[
                    TimelineMilestone(label="Horizon 1: Core Engine", date="H1 2026", status=TimelineStatus.COMPLETED),
                    TimelineMilestone(label="Horizon 2: AI Autonomy", date="H2 2026", status=TimelineStatus.CURRENT),
                    TimelineMilestone(label="Horizon 3: Global Ecosystem", date="2027+", status=TimelineStatus.PLANNED),
                ]
            ),
        ),
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Product Roadmap", topic="Strategic Vision", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_7_table() -> None:
    """Representative Deck 7: Table Summary."""
    slide = Slide(
        id="s_tbl",
        slide_number=1,
        title="Feature Tier Matrix",
        subtitle="Capabilities by subscription plan",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(
            visual_type=VisualType.TABLE,
            table_data=TableData(
                columns=[
                    TableColumn(key="feature", label="Feature"),
                    TableColumn(key="starter", label="Starter"),
                    TableColumn(key="pro", label="Pro"),
                    TableColumn(key="enterprise", label="Enterprise"),
                ],
                rows=[
                    TableRow(cells=["API Seats", "5", "50", "Unlimited"]),
                    TableRow(cells=["Custom Domain", "No", "Yes", "Yes"]),
                    TableRow(cells=["Dedicated Support", "No", "Email", "24/7 Phone + Slack"]),
                ],
            ),
        ),
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Feature Comparison", topic="Pricing & Tiers", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_8_chart() -> None:
    """Representative Deck 8: Chart Insight."""
    slide = Slide(
        id="s_chart",
        slide_number=1,
        title="Monthly Active User Growth",
        subtitle="Strong organic expansion in Q1-Q4",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(
            visual_type=VisualType.COLUMN_CHART,
            chart_data=ChartData(
                title="MAU (Millions)",
                categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                series=[ChartSeries(name="Active Users", values=[1.2, 1.8, 2.4, 3.1, 4.0, 5.2])],
            ),
        ),
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="MAU Growth", topic="Product Analytics", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_9_dense_slide() -> None:
    """Representative Deck 9: Dense 4-Card Slide."""
    slide = Slide(
        id="s_dense",
        slide_number=1,
        title="Comprehensive Cyber Defense Layers",
        subtitle="Defense-in-depth security architecture",
        narrative_role=NarrativeRole.SOLUTION,
        visual_plan=VisualPlan(visual_type=VisualType.CARD_GRID),
        elements=[
            Element(id="d1", type=ElementType.CARD, card_content=CardContent(title="Identity & IAM", body="Zero-trust Okta integration with FIDO2 hardware keys")),
            Element(id="d2", type=ElementType.CARD, card_content=CardContent(title="Network Perimeter", body="Cloudflare WAF with automated DDoS mitigation")),
            Element(id="d3", type=ElementType.CARD, card_content=CardContent(title="Runtime Security", body="Falco kernel eBPF monitoring on Kubernetes nodes")),
            Element(id="d4", type=ElementType.CARD, card_content=CardContent(title="Data Encryption", body="AES-256 at rest with AWS KMS envelope encryption")),
        ],
    )
    pres = Presentation(
        metadata=PresentationMetadata(title="Cyber Defense", topic="Security Architecture", slide_count=1),
        slides=[slide],
    )
    run_pipeline_and_verify_pptx(pres, 1)


def test_deck_10_mixed_visual_slide() -> None:
    """Representative Deck 10: Multi-Slide Mixed Deck."""
    slides = [
        Slide(
            id="m1_hero",
            slide_number=1,
            title="Antigravity Presentation System",
            subtitle="Deterministic AI PowerPoint Engine",
            narrative_role=NarrativeRole.TITLE,
            visual_plan=VisualPlan(visual_type=VisualType.HERO),
            elements=[
                Element(id="m1_t", type=ElementType.TEXT, role="title", text_content=TextContent(text="Antigravity Presentation System")),
            ],
        ),
        Slide(
            id="m2_kpi",
            slide_number=2,
            title="Generation Performance",
            subtitle="Fast sub-second rendering benchmarks",
            narrative_role=NarrativeRole.EVIDENCE,
            visual_plan=VisualPlan(visual_type=VisualType.KPI),
            elements=[
                Element(id="mk1", type=ElementType.KPI, kpi_content=KPIContent(value="<250ms", label="Layout Computation")),
                Element(id="mk2", type=ElementType.KPI, kpi_content=KPIContent(value="100%", label="Deterministic")),
            ],
        ),
    ]
    pres = Presentation(
        metadata=PresentationMetadata(title="Mixed Deck", topic="Antigravity Engine", slide_count=2),
        slides=slides,
    )
    run_pipeline_and_verify_pptx(pres, 2)
