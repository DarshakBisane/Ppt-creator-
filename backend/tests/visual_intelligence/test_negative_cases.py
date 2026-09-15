"""Negative case testing and critical semantic distinction rules."""

from backend.app.domain.elements import CardContent, Element, KPIContent, TextContent
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Slide
from backend.app.visual_intelligence.selector import SemanticVisualSelector


def test_five_stages_of_development_not_chart(make_slide) -> None:
    """'Five stages of development' should select PROCESS_FLOW / TIMELINE, NOT a chart."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Five Stages of Product Development Lifecycle",
        narrative_role=NarrativeRole.PROCESS,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Stage 1: Ideation", body="User discovery")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Stage 2: Design", body="Figma prototypes")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Stage 3: Build", body="Engineering sprint")),
            Element(id="e4", type=ElementType.CARD, card_content=CardContent(title="Stage 4: QA", body="Test automation")),
            Element(id="e5", type=ElementType.CARD, card_content=CardContent(title="Stage 5: Launch", body="General release")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type in (VisualType.PROCESS_FLOW, VisualType.TIMELINE)
    assert decision.selected_visual_type != VisualType.LINE_CHART
    assert decision.selected_visual_type != VisualType.COLUMN_CHART


def test_milestone_years_selects_timeline(make_slide) -> None:
    """'2020, 2021, 2022, 2023 milestones' should select TIMELINE."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Key Company Milestones: 2020 to 2023",
        narrative_role=NarrativeRole.TIMELINE,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="2020 Foundation", body="Company founded in SF")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="2021 Prototype", body="Alpha customer launch")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="2022 Series A", body="Scaled core platform")),
            Element(id="e4", type=ElementType.CARD, card_content=CardContent(title="2023 Global Expansion", body="Worldwide availability")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type == VisualType.TIMELINE
    assert decision.selected_archetype == "timeline"


def test_revenue_growth_with_years_selects_line_chart(make_slide) -> None:
    """'Revenue increased from 10M to 50M from 2020 to 2025' should select LINE_CHART."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Revenue Growth Over Time: 2020 to 2025 (10M to 50M ARR)",
        narrative_role=NarrativeRole.EVIDENCE,
        elements=[
            Element(id="e1", type=ElementType.KPI, kpi_content=KPIContent(value="$10M", label="2020 ARR")),
            Element(id="e2", type=ElementType.KPI, kpi_content=KPIContent(value="$25M", label="2022 ARR")),
            Element(id="e3", type=ElementType.KPI, kpi_content=KPIContent(value="$50M", label="2025 ARR")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type == VisualType.LINE_CHART
    assert decision.selected_archetype == "chart_insight"


def test_product_a_vs_b_selects_comparison(make_slide) -> None:
    """'Product A vs Product B' should select COMPARISON."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Product A vs Product B Feature Comparison",
        narrative_role=NarrativeRole.COMPARISON,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Product A (Legacy)", body="On-premise deployment with manual upgrades")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Product B (Cloud Native)", body="Serverless autonomous multi-tenant cloud")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type == VisualType.COMPARISON
    assert decision.selected_archetype == "comparison"


def test_pros_and_cons_selects_comparison(make_slide) -> None:
    """'Pros and cons of Microservices' should select COMPARISON."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Pros and Cons of Distributed Architecture",
        narrative_role=NarrativeRole.COMPARISON,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Advantages (Pros)", body="Fault isolation and independent team scaling")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Disadvantages (Cons)", body="Network latency and operational complexity")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type == VisualType.COMPARISON


def test_company_reporting_structure_selects_hierarchy(make_slide) -> None:
    """'Company reporting structure' should select HIERARCHY / TREE."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Company Department Hierarchy & Reporting Structure",
        narrative_role=NarrativeRole.CONTEXT,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="CEO & Executive Staff", body="Strategic direction")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Engineering & Product VP", body="Platform and design teams")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Sales & Operations VP", body="Go to market and support")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type in (VisualType.HIERARCHY, VisualType.TREE)
    assert decision.selected_archetype == "hierarchy_tree"


def test_api_to_auth_to_db_selects_architecture(make_slide) -> None:
    """'API Gateway -> Authentication -> Database' should select ARCHITECTURE / PROCESS_FLOW."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Cloud Architecture: API Gateway -> Authentication Service -> Database Cluster",
        narrative_role=NarrativeRole.ARCHITECTURE,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="API Gateway Layer", body="Rate limiting")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Auth Microservice", body="JWT validation")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Database Cluster", body="Persistent PostgreSQL")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type in (VisualType.ARCHITECTURE, VisualType.FLOWCHART, VisualType.PROCESS_FLOW)


def test_three_pricing_plans_selects_comparison_or_table(make_slide) -> None:
    """'Three pricing plans with features' should select COMPARISON / TABLE."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Three Pricing Plans & Feature Breakdown Matrix",
        narrative_role=NarrativeRole.COMPARISON,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Starter Tier", body="$29/mo with 5 users")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Professional Tier", body="$99/mo with unlimited users")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Enterprise Tier", body="Custom SLA and dedicated instance")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type in (VisualType.TABLE, VisualType.COMPARISON, VisualType.CARD_GRID)


def test_five_system_layers_selects_architecture(make_slide) -> None:
    """'Five system layers' should select ARCHITECTURE."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Five System Architecture Layers and Microservices Stack",
        narrative_role=NarrativeRole.ARCHITECTURE,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Layer 1: CDN", body="Cloudflare edge")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Layer 2: Load Balancer", body="AWS ALB")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Layer 3: Core App", body="Kubernetes pods")),
            Element(id="e4", type=ElementType.CARD, card_content=CardContent(title="Layer 4: Storage", body="S3 and Aurora DB")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type == VisualType.ARCHITECTURE
    assert decision.selected_archetype == "architecture"


def test_project_phases_and_future_milestones_selects_roadmap(make_slide) -> None:
    """'Project phases and future milestones' should select ROADMAP / TIMELINE."""
    selector = SemanticVisualSelector()
    slide = make_slide(
        title="Project Strategic Roadmap & Future Milestones",
        narrative_role=NarrativeRole.TIMELINE,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Phase 1: Alpha (Q1)", body="Core MVP prototype")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Phase 2: Beta (Q3)", body="Enterprise pilot tests")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Phase 3: GA (Q4)", body="Global launch")),
        ],
    )
    decision = selector.select_visual_for_slide(slide)

    assert decision.selected_visual_type in (VisualType.ROADMAP, VisualType.TIMELINE)
