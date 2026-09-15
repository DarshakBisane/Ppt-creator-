"""Deterministic Fake AI Provider for offline development and automated testing."""

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.provider import AIProvider
from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.constants import CURRENT_SCHEMA_VERSION
from backend.app.domain.content import CardContent, KPIContent, TextContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import (
    DataSource,
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


class FakeAIProvider(AIProvider):
    """Deterministic AI Provider returning valid Presentation domain blueprints without cloud APIs."""

    def __init__(
        self,
        simulate_timeout: bool = False,
        simulate_rate_limit: bool = False,
        simulate_error: bool = False,
        simulate_invalid_output: bool = False,
    ) -> None:
        self.simulate_timeout = simulate_timeout
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_error = simulate_error
        self.simulate_invalid_output = simulate_invalid_output
        self.call_count = 0

    async def generate_presentation(
        self,
        request: PresentationGenerationRequest,
    ) -> Presentation:
        """Return a deterministically constructed valid Presentation matching the request."""
        self.call_count += 1

        if self.simulate_timeout:
            raise AIProviderTimeoutError("Simulated provider timeout.")
        if self.simulate_rate_limit:
            raise AIProviderRateLimitError("Simulated rate limit exceeded.")
        if self.simulate_error:
            raise AIProviderError("Simulated AI provider failure.")
        if self.simulate_invalid_output:
            raise AIOutputValidationError("Simulated invalid output schema.")

        return self.create_deterministic_presentation(request)

    @classmethod
    def create_deterministic_presentation(cls, request: PresentationGenerationRequest) -> Presentation:
        """Create a valid Presentation domain model matching the requested slide count and topic."""
        count = request.slide_count
        topic_title = request.topic.split("\n")[0][:60].strip()

        slides: list[Slide] = []

        # Slide 1: Title / Cover Slide
        slides.append(
            Slide(
                id="slide_1",
                slide_number=1,
                title=topic_title,
                subtitle=f"A Strategic Overview | {request.purpose or 'Executive Briefing'}",
                narrative_role=NarrativeRole.TITLE,
                purpose="Hook audience and frame presentation context",
                visual_plan=VisualPlan(
                    visual_type=VisualType.NONE,
                    intent="Clean title cover layout with prominent typography",
                ),
                elements=[
                    Element(
                        id="elem_s1_title",
                        type=ElementType.TEXT,
                        role="title",
                        importance="primary",
                        text_content=TextContent(text=topic_title, emphasis=True),
                    ),
                    Element(
                        id="elem_s1_subtitle",
                        type=ElementType.TEXT,
                        role="subtitle",
                        importance="secondary",
                        text_content=TextContent(text=f"Target Audience: {request.audience or 'General'}"),
                    ),
                ],
                speaker_notes=f"Welcome everyone. Today we are presenting a strategic blueprint on {topic_title}.",
            )
        )

        # Diverse visual templates to cycle through for middle slides
        visual_templates = [
            ("Process Architecture", NarrativeRole.SOLUTION, VisualType.PROCESS_FLOW),
            ("Key Performance Indicators", NarrativeRole.EVIDENCE, VisualType.KPI),
            ("Execution Timeline", NarrativeRole.TIMELINE, VisualType.TIMELINE),
            ("Core Architectural Pillars", NarrativeRole.ARCHITECTURE, VisualType.CARD_GRID),
            ("Performance Benchmark", NarrativeRole.EVIDENCE, VisualType.COLUMN_CHART),
            ("Capability Comparison", NarrativeRole.COMPARISON, VisualType.TABLE),
        ]

        for i in range(2, count):
            template_idx = (i - 2) % len(visual_templates)
            title_prefix, narrative_role, visual_type = visual_templates[template_idx]
            slide_title = f"{title_prefix}: Phase {i - 1}"

            elements: list[Element] = []
            process_data: ProcessFlowData | None = None
            timeline_data: TimelineData | None = None
            chart_data: ChartData | None = None
            table_data: TableData | None = None

            if visual_type == VisualType.PROCESS_FLOW:
                process_data = ProcessFlowData(
                    direction=ProcessDirection.HORIZONTAL,
                    steps=[
                        ProcessStep(
                            id=f"step_{i}_1",
                            title="Discovery & Analysis",
                            description="Evaluate initial ecosystem constraints and strategic requirements.",
                            order=1,
                        ),
                        ProcessStep(
                            id=f"step_{i}_2",
                            title="Architecture Design",
                            description="Design decoupled domain modules and deterministic execution layers.",
                            order=2,
                        ),
                        ProcessStep(
                            id=f"step_{i}_3",
                            title="Deployment & Scale",
                            description="Continuous verification, monitoring, and automated delivery.",
                            order=3,
                        ),
                    ],
                )
            elif visual_type == VisualType.KPI:
                elements = [
                    Element(
                        id=f"elem_s{i}_kpi1",
                        type=ElementType.KPI,
                        role="stat",
                        importance="primary",
                        kpi_content=KPIContent(
                            label="System Availability",
                            value="99.9%",
                            context="+4.2% YoY",
                            trend="up",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_kpi2",
                        type=ElementType.KPI,
                        role="stat",
                        importance="primary",
                        kpi_content=KPIContent(
                            label="P99 Latency",
                            value="< 50ms",
                            context="-15ms improvement",
                            trend="down",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_kpi3",
                        type=ElementType.KPI,
                        role="stat",
                        importance="primary",
                        kpi_content=KPIContent(
                            label="Throughput Multiplier",
                            value="10x",
                            context="Scale-ready baseline",
                            trend="up",
                        ),
                    ),
                ]
            elif visual_type == VisualType.TIMELINE:
                timeline_data = TimelineData(
                    title="Implementation Milestones",
                    milestones=[
                        TimelineMilestone(
                            label="Phase 1: Inception",
                            date="Q1 2026",
                            description="Baseline infrastructure and domain modeling.",
                            status=TimelineStatus.COMPLETED,
                        ),
                        TimelineMilestone(
                            label="Phase 2: Alpha Rollout",
                            date="Q2 2026",
                            description="Early adopter testing and feedback integration.",
                            status=TimelineStatus.CURRENT,
                        ),
                        TimelineMilestone(
                            label="Phase 3: Production GA",
                            date="Q3 2026",
                            description="General availability and enterprise scale.",
                            status=TimelineStatus.PLANNED,
                        ),
                    ],
                )
            elif visual_type == VisualType.CARD_GRID:
                elements = [
                    Element(
                        id=f"elem_s{i}_card1",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="Reliability",
                            body="Isolated service boundaries with automatic 1-pass recovery.",
                            icon="shield",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_card2",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="Extensibility",
                            body="Provider-agnostic interfaces for multi-model AI flexibility.",
                            icon="puzzle",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_card3",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="Observability",
                            body="Structured telemetry, sanitized logs, and correlation IDs.",
                            icon="activity",
                        ),
                    ),
                ]
            elif visual_type == VisualType.COLUMN_CHART:
                chart_data = ChartData(
                    chart_type="column",
                    title="Performance Comparison",
                    categories=["Legacy System", "V1 Prototype", "Target Architecture"],
                    series=[
                        ChartSeries(
                            name="Throughput (ops/sec)",
                            values=[120.0, 450.0, 1850.0],
                        ),
                    ],
                    data_source=DataSource.ILLUSTRATIVE,
                    is_illustrative=True,
                )
            elif visual_type == VisualType.TABLE:
                table_data = TableData(
                    columns=[
                        TableColumn(key="capability", label="Capability"),
                        TableColumn(key="standard", label="Standard"),
                        TableColumn(key="enterprise", label="Enterprise"),
                    ],
                    rows=[
                        TableRow(cells=["Max Slides", "15", "30"]),
                        TableRow(cells=["Reference Transfer", "Basic", "Full Fidelity"]),
                        TableRow(cells=["Export Formats", "PPTX", "PPTX + PDF"]),
                    ],
                )

            slides.append(
                Slide(
                    id=f"slide_{i}",
                    slide_number=i,
                    title=slide_title,
                    subtitle="Strategic domain analysis and implementation mechanics",
                    narrative_role=narrative_role,
                    purpose=f"Demonstrate {title_prefix.lower()} for the presentation",
                    visual_plan=VisualPlan(
                        visual_type=visual_type,
                        intent=f"Visual layout for {visual_type.value}",
                        process_flow_data=process_data,
                        timeline_data=timeline_data,
                        chart_data=chart_data,
                        table_data=table_data,
                    ),
                    elements=elements,
                    speaker_notes=f"Key discussion points for slide {i}.",
                )
            )

        # Final Slide: Conclusion / Call to Action
        if count >= 2:
            slides.append(
                Slide(
                    id=f"slide_{count}",
                    slide_number=count,
                    title="Summary & Next Steps",
                    subtitle="Key takeaways and tactical roadmap for execution",
                    narrative_role=NarrativeRole.CONCLUSION,
                    purpose="Summarize key points and present call to action",
                    visual_plan=VisualPlan(
                        visual_type=VisualType.CARD_GRID,
                        intent="Summary takeaways in high-impact card format",
                    ),
                    elements=[
                        Element(
                            id=f"elem_s{count}_summary1",
                            type=ElementType.CARD,
                            role="card",
                            importance="primary",
                            card_content=CardContent(
                                title="Next Milestones",
                                body="Finalize architecture validation and begin deployment rollout.",
                            ),
                        ),
                        Element(
                            id=f"elem_s{count}_summary2",
                            type=ElementType.CARD,
                            role="card",
                            importance="primary",
                            card_content=CardContent(
                                title="Key Takeaway",
                                body="Decoupled AI orchestration ensures deterministic generation quality.",
                            ),
                        ),
                    ],
                    speaker_notes="Thank you for your time. Are there any questions?",
                )
            )

        design_sys = (
            request.design_context.design_system
            if request.design_context
            else DesignSystem()
        )

        return Presentation(
            schema_version=CURRENT_SCHEMA_VERSION,
            metadata=PresentationMetadata(
                title=topic_title,
                topic=request.topic,
                subtitle=f"Generated for {request.audience or 'General Audience'}",
                audience=request.audience,
                purpose=request.purpose,
                slide_count=len(slides),
                language="en",
            ),
            design_system=design_sys,
            slides=slides,
            generation_metadata={
                "provider": "fake_ai_provider",
                "mode": request.mode,
            },
        )
