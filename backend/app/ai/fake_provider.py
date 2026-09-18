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
from backend.app.domain.palettes import ProfessionalPaletteGenerator
from backend.app.domain.presentation import (
    GenerationMetadata,
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
from backend.app.rendering.icons import get_semantic_icon


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
        """Create a valid, executive-grade Presentation domain model matching the requested slide count and topic."""
        count = request.slide_count
        topic_title = request.topic.split("\n")[0][:60].strip()

        slides: list[Slide] = []

        # Slide 1: Title / Cover Slide
        slides.append(
            Slide(
                id="slide_1",
                slide_number=1,
                title=topic_title,
                subtitle=f"A Strategic and Architectural Overview | {request.purpose or 'Executive Briefing'}",
                narrative_role=NarrativeRole.TITLE,
                purpose="Hook audience and frame presentation context",
                takeaway="Strategic infrastructure scalability hinges on decoupled deterministic architecture.",
                visual_plan=VisualPlan(
                    visual_type=VisualType.NONE,
                    intent="Executive Title Cover Layout with high-impact typography",
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
                speaker_notes=f"Welcome everyone. Today we are presenting an architectural deep dive on {topic_title}.",
            )
        )

        # Diverse professional diagram and visual templates for middle slides
        visual_templates = [
            (
                "System Structural Anatomy & Core Parameters",
                "Detailed schema composition and cryptographic binding properties",
                NarrativeRole.ARCHITECTURE,
                VisualType.ANATOMY,
                "Central structural object with labeled callout components",
                "Ensure strong component isolation and cryptographic parameter enforcement.",
            ),
            (
                "End-to-End Operational Lifecycle Pipeline",
                "Step-by-step workflow from provisioning to continuous validation",
                NarrativeRole.PROCESS,
                VisualType.LIFECYCLE,
                "Sequential lifecycle flow with transition arrows",
                "Automate key lifecycle stages to minimize manual operational overhead.",
            ),
            (
                "Multi-Tier Architecture & Protocol Integration",
                "Decoupled service layers ensuring high availability and fault isolation",
                NarrativeRole.SOLUTION,
                VisualType.LAYERED_STACK,
                "Stacked hierarchical architecture layers",
                "Layered separation of concerns guarantees horizontal scale and zero single points of failure.",
            ),
            (
                "Verification Decision Tree & Integrity Checks",
                "Deterministic validation sequence applied against corporate trust anchors",
                NarrativeRole.EVIDENCE,
                VisualType.DECISION_FLOW,
                "Decision checkpoint pipeline with trust verification node",
                "Strict multi-checkpoint validation prevents spoofing and stale revocation issues.",
            ),
            (
                "Key Performance Metrics & Operational Velocity",
                "Empirical benchmarks demonstrating throughput gains and latency reductions",
                NarrativeRole.EVIDENCE,
                VisualType.KPI,
                "High-impact KPI metric dashboard",
                "Production telemetry demonstrates measurable velocity gains across all pipelines.",
            ),
            (
                "Strategic Architectural Comparison Matrix",
                "Evaluating capability tradeoffs against legacy operational patterns",
                NarrativeRole.COMPARISON,
                VisualType.TABLE,
                "Structured capability comparison matrix",
                "Modern decoupled design significantly outperforms monolithic legacy patterns.",
            ),
        ]

        for i in range(2, count):
            template_idx = (i - 2) % len(visual_templates)
            slide_title, slide_subtitle, narrative_role, visual_type, v_intent, takeaway = visual_templates[template_idx]

            elements: list[Element] = []
            process_data: ProcessFlowData | None = None
            timeline_data: TimelineData | None = None
            chart_data: ChartData | None = None
            table_data: TableData | None = None

            if visual_type == VisualType.ANATOMY:
                elements = [
                    Element(
                        id=f"elem_s{i}_c1",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="Version & Identity",
                            body="RFC compliance and Distinguished Name attributes.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_c2",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Key Material & OID",
                            body="Asymmetric cryptographic key parameters and curve identifiers.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_c3",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="CA Digital Signature",
                            body="Cryptographic proof of integrity signed by issuing authority.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_c4",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Validity & Extensions",
                            body="SAN attributes, Key Usage constraints, and CRL distribution points.",
                        ),
                    ),
                ]
            elif visual_type == VisualType.LIFECYCLE:
                elements = [
                    Element(
                        id=f"elem_s{i}_step1",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="01  Key Generation",
                            body="Client generates asymmetric key pair in secure storage.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_step2",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="02  CSR Validation",
                            body="RA validates domain ownership and identity policy.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_step3",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="03  CA Issuance",
                            body="CA signs and publishes certificate bundle.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_step4",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="04  Monitoring",
                            body="Automated telemetry tracks expiration and OCSP status.",
                        ),
                    ),
                ]
            elif visual_type == VisualType.LAYERED_STACK:
                elements = [
                    Element(
                        id=f"elem_s{i}_l1",
                        type=ElementType.CARD,
                        role="card",
                        importance="primary",
                        card_content=CardContent(
                            title="Client & Ingress Layer",
                            body="Microservices, web clients, and automated API agents.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_l2",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Orchestration & Vault Tier",
                            body="Automated policy controllers, secret engines, and cert-manager.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_l3",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Core Authority Engine",
                            body="Root and Subordinate CAs managing key issuance pipelines.",
                        ),
                    ),
                ]
            elif visual_type == VisualType.DECISION_FLOW:
                elements = [
                    Element(
                        id=f"elem_s{i}_df1",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Certificate Ingestion",
                            body="Client receives TLS payload during handshake.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_df2",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Trust Anchor Check",
                            body="Verify issuing CA exists in trusted root store.",
                        ),
                    ),
                    Element(
                        id=f"elem_s{i}_df3",
                        type=ElementType.CARD,
                        role="card",
                        importance="secondary",
                        card_content=CardContent(
                            title="Signature & Revocation",
                            body="Validate CA signature and check real-time OCSP response.",
                        ),
                    ),
                ]
            elif visual_type == VisualType.KPI:
                elements = [
                    Element(
                        id=f"elem_s{i}_kpi1",
                        type=ElementType.KPI,
                        role="stat",
                        importance="primary",
                        kpi_content=KPIContent(
                            label="System Availability",
                            value="99.99%",
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
                            label="P99 Validation Latency",
                            value="< 12ms",
                            context="-15ms reduction",
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
                            value="12x",
                            context="Production baseline",
                            trend="up",
                        ),
                    ),
                ]
            elif visual_type == VisualType.TABLE:
                table_data = TableData(
                    columns=[
                        TableColumn(key="dim", label="Architecture Dimension"),
                        TableColumn(key="standard", label="Target Architecture"),
                        TableColumn(key="legacy", label="Legacy Infrastructure"),
                    ],
                    rows=[
                        TableRow(cells=["Issuance Automation", "Zero-Touch API / ACME", "Manual Ticket Workflow"]),
                        TableRow(cells=["Revocation Check", "Real-time OCSP Stapling", "Static Uncached CRLs"]),
                        TableRow(cells=["Failure Resilience", "Decoupled Multi-Tier CAs", "Single Point of Failure"]),
                    ],
                )

            slides.append(
                Slide(
                    id=f"slide_{i}",
                    slide_number=i,
                    title=slide_title,
                    subtitle=slide_subtitle,
                    narrative_role=narrative_role,
                    purpose=f"Demonstrate {slide_title} for the presentation",
                    takeaway=takeaway,
                    visual_plan=VisualPlan(
                        visual_type=visual_type,
                        intent=v_intent,
                        process_flow_data=process_data,
                        timeline_data=timeline_data,
                        chart_data=chart_data,
                        table_data=table_data,
                    ),
                    elements=elements,
                    speaker_notes=f"Key discussion points for slide {i}.",
                )
            )

        # Final Slide: Conclusion / Strategic Roadmap
        if count >= 2:
            slides.append(
                Slide(
                    id=f"slide_{count}",
                    slide_number=count,
                    title="Executive Summary & Strategic Roadmap",
                    subtitle="Key operational imperatives and implementation timeline",
                    narrative_role=NarrativeRole.CONCLUSION,
                    purpose="Summarize key points and present strategic roadmap",
                    takeaway="Adopt a phased automation model to establish enduring security governance and operational velocity.",
                    visual_plan=VisualPlan(
                        visual_type=VisualType.ROADMAP,
                        intent="Strategic roadmap in phased swimlane format",
                    ),
                    elements=[
                        Element(
                            id=f"elem_s{count}_r1",
                            type=ElementType.CARD,
                            role="card",
                            importance="primary",
                            card_content=CardContent(
                                title="Phase 1: Architecture",
                                body="Finalize decoupled authority boundaries and hardware security modules.",
                            ),
                        ),
                        Element(
                            id=f"elem_s{count}_r2",
                            type=ElementType.CARD,
                            role="card",
                            importance="secondary",
                            card_content=CardContent(
                                title="Phase 2: Automation",
                                body="Integrate ACME protocol and cert-manager into CI/CD delivery pipelines.",
                            ),
                        ),
                        Element(
                            id=f"elem_s{count}_r3",
                            type=ElementType.CARD,
                            role="card",
                            importance="secondary",
                            card_content=CardContent(
                                title="Phase 3: Scale",
                                body="Full enterprise rollout with real-time OCSP monitoring and SLA governance.",
                            ),
                        ),
                    ],
                    speaker_notes="Thank you for your time. We are now open for questions and strategic discussion.",
                )
            )

        if request.design_context and request.design_context.design_system:
            design_sys = request.design_context.design_system
        else:
            palette = ProfessionalPaletteGenerator.create_palette(
                topic=request.topic,
                audience=request.audience,
            )
            design_sys = DesignSystem(palette=palette)

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
            generation_metadata=GenerationMetadata(
                provider="fake_ai_provider",
                mode=request.mode,
            ),
        )
