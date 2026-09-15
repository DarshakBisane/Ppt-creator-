"""Pytest fixtures and slide factory helpers for visual intelligence tests."""

import pytest
from backend.app.domain.elements import CardContent, Element, KPIContent, TextContent
from backend.app.domain.enums import ElementType, NarrativeRole, VisualType
from backend.app.domain.presentation import Presentation, PresentationMetadata, Slide
from backend.app.domain.visuals import VisualPlan


@pytest.fixture
def make_slide():
    """Factory helper creating slides with custom titles, roles, elements, and visual plans."""
    def _factory(
        title: str = "Overview",
        narrative_role: NarrativeRole = NarrativeRole.CONTEXT,
        subtitle: str = "",
        elements: list[Element] | None = None,
        visual_type: VisualType = VisualType.NONE,
        slide_number: int = 1,
    ) -> Slide:
        return Slide(
            id=f"slide_{slide_number}",
            slide_number=slide_number,
            title=title,
            subtitle=subtitle,
            narrative_role=narrative_role,
            visual_plan=VisualPlan(visual_type=visual_type),
            elements=elements or [],
        )
    return _factory


@pytest.fixture
def process_slide(make_slide) -> Slide:
    """Slide describing sequential execution workflow."""
    return make_slide(
        title="Engineering Deployment Pipeline Workflow",
        narrative_role=NarrativeRole.PROCESS,
        elements=[
            Element(id="e1", type=ElementType.CARD, card_content=CardContent(title="Step 1: Code Commit", body="Automated linting and test runs")),
            Element(id="e2", type=ElementType.CARD, card_content=CardContent(title="Step 2: Build & Package", body="Docker image build and artifact scan")),
            Element(id="e3", type=ElementType.CARD, card_content=CardContent(title="Step 3: Staging Deploy", body="Integration and smoke tests")),
            Element(id="e4", type=ElementType.CARD, card_content=CardContent(title="Step 4: Canary Production", body="Traffic ramp and metrics monitoring")),
        ],
    )


@pytest.fixture
def timeline_slide(make_slide) -> Slide:
    """Slide describing strategic multi-year milestones."""
    return make_slide(
        title="Enterprise Evolution Timeline & Milestones",
        narrative_role=NarrativeRole.TIMELINE,
        elements=[
            Element(id="t1", type=ElementType.CARD, card_content=CardContent(title="2021 Founding", body="Seed round and core platform prototype")),
            Element(id="t2", type=ElementType.CARD, card_content=CardContent(title="2023 Series A", body="Market expansion and 100 enterprise customers")),
            Element(id="t3", type=ElementType.CARD, card_content=CardContent(title="2025 Global Scale", body="International data centers and SOC2 compliance")),
            Element(id="t4", type=ElementType.CARD, card_content=CardContent(title="2026 AI Autonomy", body="Fully autonomous agentic workflows")),
        ],
    )


@pytest.fixture
def comparison_slide(make_slide) -> Slide:
    """Slide comparing two architectural approaches."""
    return make_slide(
        title="Monolithic Architecture vs Microservices Architecture Comparison",
        narrative_role=NarrativeRole.COMPARISON,
        elements=[
            Element(id="c1", type=ElementType.CARD, card_content=CardContent(title="Monolithic Approach", body="Single deployment unit with high database coupling")),
            Element(id="c2", type=ElementType.CARD, card_content=CardContent(title="Microservices Approach", body="Decoupled independent services with event-driven sync")),
        ],
    )


@pytest.fixture
def quantitative_slide(make_slide) -> Slide:
    """Slide with continuous revenue metrics over years."""
    return make_slide(
        title="Annual Recurring Revenue Growth 2021 to 2025",
        narrative_role=NarrativeRole.EVIDENCE,
        elements=[
            Element(id="q1", type=ElementType.KPI, kpi_content=KPIContent(value="$12M", label="2021 ARR")),
            Element(id="q2", type=ElementType.KPI, kpi_content=KPIContent(value="$28M", label="2023 ARR")),
            Element(id="q3", type=ElementType.KPI, kpi_content=KPIContent(value="$65M", label="2025 ARR")),
        ],
    )


@pytest.fixture
def architecture_slide(make_slide) -> Slide:
    """Slide describing multi-tier cloud infrastructure."""
    return make_slide(
        title="Core System Cloud Architecture and Infrastructure",
        narrative_role=NarrativeRole.ARCHITECTURE,
        elements=[
            Element(id="a1", type=ElementType.CARD, card_content=CardContent(title="Layer 1: Edge CDN & API Gateway", body="TLS termination and rate limiting")),
            Element(id="a2", type=ElementType.CARD, card_content=CardContent(title="Layer 2: Microservices Cluster", body="Containerized core business logic services")),
            Element(id="a3", type=ElementType.CARD, card_content=CardContent(title="Layer 3: Distributed Database & Cache", body="PostgreSQL cluster and Redis memory caching")),
        ],
    )
