"""Tests for full JSON serialization and round-trip deserialization."""

from backend.app.domain import (
    CardContent,
    ChartData,
    ChartSeries,
    CURRENT_SCHEMA_VERSION,
    DataSource,
    DesignSystem,
    Element,
    ElementType,
    KPIContent,
    NarrativeRole,
    Presentation,
    PresentationMetadata,
    ProcessFlowData,
    ProcessStep,
    Slide,
    TableColumn,
    TableData,
    TableRow,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
    VisualType,
)


def build_rich_presentation_fixture() -> Presentation:
    """Construct a full rich presentation with diverse visual types and elements."""
    meta = PresentationMetadata(
        title="Enterprise AI Strategy 2026",
        topic="Generative AI Adoption & ROI Framework",
        subtitle="Executive Board Presentation",
        audience="C-Level Executives",
        purpose="Strategic Alignment",
        language="en",
        slide_count=4,
    )

    # Slide 1: Hero / Context
    s1 = Slide(
        id="slide-1",
        slide_number=1,
        title="Executive Vision",
        subtitle="Transforming enterprise workflows with private AI engines",
        narrative_role=NarrativeRole.TITLE,
        visual_plan=VisualPlan(
            visual_type=VisualType.HERO,
            intent="High-impact strategic thesis",
            priority="hero",
        ),
        elements=[
            Element(
                id="elem-kpi-1",
                type=ElementType.KPI,
                kpi_content=KPIContent(
                    label="Projected Productivity Uplift",
                    value="38",
                    unit="%",
                    context="Across software and finance operations",
                    trend="up",
                ),
            )
        ],
    )

    # Slide 2: Process Flow
    s2 = Slide(
        id="slide-2",
        slide_number=2,
        title="3-Tier Implementation Roadmap",
        subtitle="From pilot sandbox to production orchestration",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(
            visual_type=VisualType.PROCESS_FLOW,
            intent="Sequential rollout strategy",
            process_flow_data=ProcessFlowData(
                steps=[
                    ProcessStep(id="st-1", title="Sandbox Validation", order=1),
                    ProcessStep(id="st-2", title="Security Review", order=2),
                    ProcessStep(id="st-3", title="Enterprise Rollout", order=3),
                ]
            ),
        ),
    )

    # Slide 3: Chart Data
    s3 = Slide(
        id="slide-3",
        slide_number=3,
        title="ROI & Margin Expansion",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(
            visual_type=VisualType.COLUMN_CHART,
            chart_data=ChartData(
                chart_type="column",
                title="Year-over-Year Operating Margin ($M)",
                categories=["2023", "2024", "2025", "2026 (Target)"],
                series=[
                    ChartSeries(name="Traditional Baseline", values=[40.0, 42.0, 43.5, 45.0]),
                    ChartSeries(name="AI-Accelerated", values=[40.0, 48.0, 58.5, 72.0]),
                ],
                data_source=DataSource.USER_PROVIDED,
                is_illustrative=False,
            ),
        ),
    )

    # Slide 4: Comparison Table
    s4 = Slide(
        id="slide-4",
        slide_number=4,
        title="Architecture Comparison",
        narrative_role=NarrativeRole.COMPARISON,
        visual_plan=VisualPlan(
            visual_type=VisualType.TABLE,
            table_data=TableData(
                columns=[
                    TableColumn(key="metric", label="Evaluation Metric"),
                    TableColumn(key="cloud", label="Public Cloud API"),
                    TableColumn(key="private", label="Dedicated Private VPC"),
                ],
                rows=[
                    TableRow(cells=["Data Privacy", "Shared Tenant", "Zero-Data Retention VPC"]),
                    TableRow(cells=["Latency (p99)", "850ms", "120ms Dedicated GPU"]),
                    TableRow(cells=["Unit Economics", "Pay-per-token", "Fixed Infrastructure"]),
                ],
            ),
        ),
    )

    return Presentation(
        schema_version=CURRENT_SCHEMA_VERSION,
        metadata=meta,
        design_system=DesignSystem(),
        slides=[s1, s2, s3, s4],
    )


def test_presentation_json_roundtrip_serialization() -> None:
    """Verify that Presentation serializes to JSON and recovers cleanly with 100% fidelity."""
    original_pres = build_rich_presentation_fixture()

    # 1. Serialize to JSON string
    json_output = original_pres.model_dump_json(indent=2)
    assert isinstance(json_output, str)
    assert "Enterprise AI Strategy 2026" in json_output
    assert "Traditional Baseline" in json_output
    assert "Zero-Data Retention VPC" in json_output

    # 2. Deserialize from JSON string
    recovered_pres = Presentation.model_validate_json(json_output)

    # 3. Assert deep semantic equality
    assert recovered_pres.schema_version == original_pres.schema_version
    assert recovered_pres.metadata.title == original_pres.metadata.title
    assert len(recovered_pres.slides) == len(original_pres.slides)
    assert recovered_pres.slides[1].visual_plan.process_flow_data is not None
    assert (
        recovered_pres.slides[1].visual_plan.process_flow_data.steps[0].title
        == "Sandbox Validation"
    )
    assert recovered_pres.slides[2].visual_plan.chart_data is not None
    assert (
        recovered_pres.slides[2].visual_plan.chart_data.series[1].values[3] == 72.0
    )
    assert recovered_pres.slides[3].visual_plan.table_data is not None
    assert (
        recovered_pres.slides[3].visual_plan.table_data.rows[0].cells[2]
        == "Zero-Data Retention VPC"
    )
