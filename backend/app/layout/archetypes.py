"""Deterministic layout archetypes converting semantic content into geometric coordinates."""

from abc import ABC, abstractmethod
from typing import Any

from backend.app.domain.enums import (
    Alignment,
    ElementType,
    ProcessDirection,
    TimelineStatus,
    VisualType,
)
from backend.app.domain.presentation import Slide
from backend.app.domain.visuals import ProcessFlowData, ProcessStep, TimelineData, TimelineMilestone
from backend.app.layout.models import (
    ConnectorGeometry,
    ConnectorPort,
    ElementGeometry,
    LayoutWarning,
    Rect,
)
from backend.app.layout.spacing import (
    SpacingContext,
    calculate_card_column,
    calculate_card_row,
    calculate_grid,
    calculate_split,
    distribute_horizontal,
    distribute_vertical,
    generate_ports,
)


class BaseArchetypeResolver(ABC):
    """Abstract base class for deterministic layout resolvers."""

    @abstractmethod
    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        """Resolve semantic slide content into concrete geometries and connectors."""
        pass


# ---------------------------------------------------------------------------
# 1. Blank / Freeform Layout
# ---------------------------------------------------------------------------
class BlankResolver(BaseArchetypeResolver):
    """Clean minimal / freeform container layout."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        if not slide.elements:
            # Create a single safe canvas container
            rect = content_rect.inset(ctx.card_padding, ctx.card_padding)
            geom = ElementGeometry(
                id=f"{slide.id}_canvas_panel",
                semantic_type=ElementType.CARD,
                rect=rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(f"{slide.id}_canvas_panel", rect),
                role="canvas",
            )
            elements.append(geom)
            return elements, [], warnings

        count = len(slide.elements)
        if count == 1:
            elem = slide.elements[0]
            geom = ElementGeometry(
                id=elem.id,
                semantic_type=elem.type,
                rect=content_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(elem.id, content_rect),
                role=elem.role,
                importance=elem.importance,
                content_data=elem.text_content or elem.card_content or elem,
            )
            elements.append(geom)
        else:
            card_rects = calculate_card_row(content_rect, count, ctx.card_gap)
            for elem, r in zip(slide.elements, card_rects):
                geom = ElementGeometry(
                    id=elem.id,
                    semantic_type=elem.type,
                    rect=r,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(elem.id, r),
                    role=elem.role,
                    importance=elem.importance,
                    content_data=elem.text_content or elem.card_content or elem,
                )
                elements.append(geom)

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 2. Title + Body Layout
# ---------------------------------------------------------------------------
class TitleBodyResolver(BaseArchetypeResolver):
    """Narrative text layout with lead statement and structured body blocks."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        # Split into main lead card (top) and detailed body card (bottom) or two columns
        lead_height = round(content_rect.height * 0.35)
        body_height = content_rect.height - lead_height - ctx.row_gap

        lead_rect = Rect(
            x=content_rect.x,
            y=content_rect.y,
            width=content_rect.width,
            height=lead_height,
        )
        body_rect = Rect(
            x=content_rect.x,
            y=content_rect.y + lead_height + ctx.row_gap,
            width=content_rect.width,
            height=body_height,
        )

        # Primary Lead / Narrative summary
        lead_id = f"{slide.id}_lead_block"
        lead_text = slide.purpose or (slide.elements[0].text_content.text if slide.elements and slide.elements[0].text_content else slide.title)
        elements.append(
            ElementGeometry(
                id=lead_id,
                semantic_type=ElementType.CARD,
                rect=lead_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(lead_id, lead_rect),
                role="lead",
                importance="primary",
                style_hints={"variant": "lead_card", "padding": ctx.card_padding},
                content_data={"title": "Executive Summary", "text": lead_text},
            )
        )

        # Body supporting points
        body_id = f"{slide.id}_body_block"
        supporting_items = [
            elem.text_content.text if elem.text_content else elem.role
            for elem in slide.elements[1:]
        ] if len(slide.elements) > 1 else [
            "Structured implementation details and operational context.",
            "Key strategic takeaways aligned with organizational objectives.",
            "Cross-functional impact and continuous delivery metrics.",
        ]

        elements.append(
            ElementGeometry(
                id=body_id,
                semantic_type=ElementType.CARD,
                rect=body_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(body_id, body_rect),
                role="body",
                importance="secondary",
                style_hints={"variant": "bullet_card", "padding": ctx.card_padding},
                content_data={"items": supporting_items},
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 3. Hero Layout
# ---------------------------------------------------------------------------
class HeroResolver(BaseArchetypeResolver):
    """Dramatic focal card with prominent typography and key impact metric."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        left_w = round(content_rect.width * 0.65)
        right_w = content_rect.width - left_w - ctx.column_gap

        hero_rect = Rect(x=content_rect.x, y=content_rect.y, width=left_w, height=content_rect.height)
        sidebar_rect = Rect(
            x=content_rect.x + left_w + ctx.column_gap,
            y=content_rect.y,
            width=right_w,
            height=content_rect.height,
        )

        hero_id = f"{slide.id}_hero_main"
        sidebar_id = f"{slide.id}_hero_impact"

        hero_headline = slide.title
        hero_body = slide.purpose or (slide.subtitle or "Transformative technological and operational capabilities.")

        elements.append(
            ElementGeometry(
                id=hero_id,
                semantic_type=ElementType.CARD,
                rect=hero_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(hero_id, hero_rect),
                role="hero",
                importance="primary",
                style_hints={"variant": "hero_banner", "accent_border": True},
                content_data={"headline": hero_headline, "body": hero_body},
            )
        )

        elements.append(
            ElementGeometry(
                id=sidebar_id,
                semantic_type=ElementType.CARD,
                rect=sidebar_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(sidebar_id, sidebar_rect),
                role="kpi",
                importance="accent",
                style_hints={"variant": "metric_callout"},
                content_data={
                    "metric": "10x",
                    "label": "Performance Velocity",
                    "subtext": "Measurable impact across production workflows.",
                },
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 4. Two Column Layout
# ---------------------------------------------------------------------------
class TwoColumnResolver(BaseArchetypeResolver):
    """Split 50/50 or 60/40 two-column layout."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        left_rect, right_rect = calculate_split(content_rect, left_ratio=0.5, gap=ctx.column_gap)

        left_elem = slide.elements[0] if len(slide.elements) > 0 else None
        right_elem = slide.elements[1] if len(slide.elements) > 1 else None

        left_id = left_elem.id if left_elem else f"{slide.id}_col_1"
        right_id = right_elem.id if right_elem else f"{slide.id}_col_2"

        elements.append(
            ElementGeometry(
                id=left_id,
                semantic_type=left_elem.type if left_elem else ElementType.CARD,
                rect=left_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(left_id, left_rect),
                role="column_left",
                importance="primary",
                content_data=left_elem.card_content or left_elem.text_content if left_elem else {
                    "title": "Primary Architecture",
                    "body": "Decoupled domain specifications with strict schema validation and typing.",
                },
            )
        )

        elements.append(
            ElementGeometry(
                id=right_id,
                semantic_type=right_elem.type if right_elem else ElementType.CARD,
                rect=right_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(right_id, right_rect),
                role="column_right",
                importance="secondary",
                content_data=right_elem.card_content or right_elem.text_content if right_elem else {
                    "title": "Execution Strategy",
                    "body": "Deterministic spatial calculation guaranteeing visual harmony and zero drift.",
                },
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 5. Three Card Row Layout
# ---------------------------------------------------------------------------
class ThreeCardRowResolver(BaseArchetypeResolver):
    """Horizontal 3-card card row with balanced spacing and header icons/metrics."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        card_rects = calculate_card_row(content_rect, count=3, gap=ctx.card_gap)

        default_cards = [
            {"title": "Scalability", "body": "Handles multi-tenant workloads with sub-second layout calculation.", "icon": "Layers"},
            {"title": "Determinism", "body": "Identical layout results for identical inputs with zero drift.", "icon": "Cpu"},
            {"title": "Extensibility", "body": "Pluggable archetype registry supporting bespoke visual models.", "icon": "Boxes"},
        ]

        for i, rect in enumerate(card_rects):
            elem = slide.elements[i] if i < len(slide.elements) else None
            card_id = elem.id if elem else f"{slide.id}_card_{i+1}"
            content = elem.card_content.model_dump() if elem and elem.card_content else default_cards[i]

            geom = ElementGeometry(
                id=card_id,
                semantic_type=ElementType.CARD,
                rect=rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(card_id, rect),
                role="card",
                importance="primary" if i == 0 else "secondary",
                content_data=content,
            )
            elements.append(geom)

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 6. Four Card Grid Layout
# ---------------------------------------------------------------------------
class FourCardGridResolver(BaseArchetypeResolver):
    """2x2 responsive card grid with uniform row and column spacing."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        grid = calculate_grid(content_rect, cols=2, rows=2, col_gap=ctx.column_gap, row_gap=ctx.row_gap)
        flat_rects = [cell for row in grid for cell in row]

        default_items = [
            {"title": "Core Domain", "body": "Decoupled business logic without rendering baggage."},
            {"title": "Layout Engine", "body": "Mathematical 1920x1080 coordinate resolution."},
            {"title": "PPTX Renderer", "body": "Native OpenXML shape and table generation."},
            {"title": "Visual QA", "body": "Automated collision and aesthetic validation."},
        ]

        for i, rect in enumerate(flat_rects):
            elem = slide.elements[i] if i < len(slide.elements) else None
            card_id = elem.id if elem else f"{slide.id}_grid_card_{i+1}"
            content = elem.card_content.model_dump() if elem and elem.card_content else default_items[i]

            elements.append(
                ElementGeometry(
                    id=card_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=generate_ports(card_id, rect),
                    role="grid_cell",
                    importance="secondary",
                    content_data=content,
                )
            )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 7. KPI Dashboard Layout
# ---------------------------------------------------------------------------
class KPIDashboardResolver(BaseArchetypeResolver):
    """Prominent KPI metric block cards (3 or 4 metrics) with trend indicators."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        count = len(slide.elements) if 2 <= len(slide.elements) <= 4 else 3
        card_rects = calculate_card_row(content_rect, count=count, gap=ctx.card_gap)

        default_kpis = [
            {"value": "99.9%", "unit": "Uptime", "label": "System Reliability", "trend": "up", "context": "Enterprise SLA target exceeded"},
            {"value": "<50ms", "unit": "Latency", "label": "Layout Resolution", "trend": "up", "context": "Deterministic algorithmic execution"},
            {"value": "100%", "unit": "Native", "label": "OpenXML Shapes", "trend": "neutral", "context": "Zero slide rasterization"},
            {"value": "4.9/5", "unit": "Score", "label": "Design Fidelity", "trend": "up", "context": "Audited by visual QA"},
        ]

        for i, rect in enumerate(card_rects):
            elem = slide.elements[i] if i < len(slide.elements) else None
            kpi_id = elem.id if elem else f"{slide.id}_kpi_{i+1}"
            content = elem.kpi_content.model_dump() if elem and elem.kpi_content else default_kpis[i % len(default_kpis)]

            elements.append(
                ElementGeometry(
                    id=kpi_id,
                    semantic_type=ElementType.KPI,
                    rect=rect,
                    alignment=Alignment.CENTER,
                    ports=generate_ports(kpi_id, rect),
                    role="kpi_metric",
                    importance="primary" if i == 0 else "secondary",
                    content_data=content,
                )
            )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 8. Comparison (Split) Layout
# ---------------------------------------------------------------------------
class ComparisonResolver(BaseArchetypeResolver):
    """Side-by-side comparative layout with center divider."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        divider_width = 56
        badge_gap = ctx.card_gap
        total_divider_span = divider_width + (2 * badge_gap)
        available_w = content_rect.width - total_divider_span
        panel_w = available_w // 2

        left_rect = Rect(x=content_rect.x, y=content_rect.y, width=panel_w, height=content_rect.height)
        vs_x = content_rect.x + panel_w + badge_gap
        vs_rect = Rect(
            x=vs_x,
            y=content_rect.center_y - 28,
            width=divider_width,
            height=56,
        )
        right_rect = Rect(
            x=vs_rect.right + badge_gap,
            y=content_rect.y,
            width=panel_w,
            height=content_rect.height,
        )

        left_id = f"{slide.id}_compare_left"
        right_id = f"{slide.id}_compare_right"
        vs_id = f"{slide.id}_compare_vs"

        elements.append(
            ElementGeometry(
                id=left_id,
                semantic_type=ElementType.CARD,
                rect=left_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(left_id, left_rect),
                role="comparison_left",
                importance="primary",
                style_hints={"variant": "comparison_panel", "theme": "surface"},
                content_data={"title": "Option A / Traditional", "points": ["Manual layout adjustments", "Fragile shape positioning", "High maintenance overhead"]},
            )
        )

        elements.append(
            ElementGeometry(
                id=vs_id,
                semantic_type=ElementType.SHAPE,
                rect=vs_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(vs_id, vs_rect),
                role="vs_badge",
                importance="accent",
                style_hints={"variant": "pill", "text": "VS"},
            )
        )

        elements.append(
            ElementGeometry(
                id=right_id,
                semantic_type=ElementType.CARD,
                rect=right_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(right_id, right_rect),
                role="comparison_right",
                importance="primary",
                style_hints={"variant": "comparison_panel", "theme": "primary_tint"},
                content_data={"title": "Option B / PresenAI", "points": ["Deterministic 1920x1080 layout", "Native OpenXML editable shapes", "Sub-second batch generation"]},
            )
        )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 9. Timeline Layout
# ---------------------------------------------------------------------------
class TimelineResolver(BaseArchetypeResolver):
    """Horizontal milestone spine with alternating milestone cards."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        t_data: TimelineData | None = slide.visual_plan.timeline_data
        milestones = t_data.milestones if t_data and t_data.milestones else [
            TimelineMilestone(label="Phase 1", date="Q1 2026", description="Architecture & Domain Schemas", status=TimelineStatus.COMPLETED),
            TimelineMilestone(label="Phase 2", date="Q2 2026", description="Deterministic Layout Engine", status=TimelineStatus.CURRENT),
            TimelineMilestone(label="Phase 3", date="Q3 2026", description="Native PPTX & Visual QA", status=TimelineStatus.PLANNED),
            TimelineMilestone(label="Phase 4", date="Q4 2026", description="Enterprise Production Release", status=TimelineStatus.PLANNED),
        ]

        count = len(milestones)
        spine_y = content_rect.center_y
        spine_id = f"{slide.id}_timeline_spine"

        # Central spine bar
        spine_rect = Rect(x=content_rect.x, y=spine_y - 2, width=content_rect.width, height=4)
        elements.append(
            ElementGeometry(
                id=spine_id,
                semantic_type=ElementType.SHAPE,
                rect=spine_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(spine_id, spine_rect),
                role="spine",
                importance="secondary",
            )
        )

        col_slices = distribute_horizontal(content_rect.width, count, gap=ctx.card_gap)
        card_h = (content_rect.height // 2) - 40

        for i, (offset_x, col_w) in enumerate(col_slices):
            m = milestones[i]
            node_x = content_rect.x + offset_x + (col_w // 2)
            node_id = f"{slide.id}_node_{i+1}"
            card_id = f"{slide.id}_milestone_{i+1}"

            # Milestone node dot on spine
            node_rect = Rect(x=node_x - 10, y=spine_y - 10, width=20, height=20)
            node_ports = generate_ports(node_id, node_rect)
            elements.append(
                ElementGeometry(
                    id=node_id,
                    semantic_type=ElementType.SHAPE,
                    rect=node_rect,
                    alignment=Alignment.CENTER,
                    ports=node_ports,
                    role="timeline_node",
                    importance="primary" if m.status == TimelineStatus.CURRENT else "secondary",
                    style_hints={"status": m.status.value},
                )
            )

            # Alternate cards above and below spine
            is_above = (i % 2 == 0)
            card_y = (spine_y - 30 - card_h) if is_above else (spine_y + 30)
            card_rect = Rect(x=content_rect.x + offset_x, y=card_y, width=col_w, height=card_h)
            card_ports = generate_ports(card_id, card_rect)

            elements.append(
                ElementGeometry(
                    id=card_id,
                    semantic_type=ElementType.CARD,
                    rect=card_rect,
                    alignment=Alignment.LEFT,
                    ports=card_ports,
                    role="milestone_card",
                    importance="primary" if m.status == TimelineStatus.CURRENT else "secondary",
                    content_data={
                        "date": m.date,
                        "label": m.label,
                        "description": m.description,
                        "status": m.status.value,
                    },
                )
            )

            # Connector line between node and card
            connectors.append(
                ConnectorGeometry(
                    id=f"{slide.id}_conn_{i+1}",
                    start_port_id=f"{node_id}_port_top" if is_above else f"{node_id}_port_bottom",
                    end_port_id=f"{card_id}_port_bottom" if is_above else f"{card_id}_port_top",
                    start_x=node_x,
                    start_y=spine_y - 10 if is_above else spine_y + 10,
                    end_x=node_x,
                    end_y=card_rect.bottom if is_above else card_rect.y,
                    connector_type="line",
                    stroke_width=2,
                )
            )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 10. Process Flow Layout
# ---------------------------------------------------------------------------
class ProcessFlowResolver(BaseArchetypeResolver):
    """Sequential step cards with directional chevron/arrow connectors."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        pf_data: ProcessFlowData | None = slide.visual_plan.process_flow_data
        steps = pf_data.steps if pf_data and pf_data.steps else [
            ProcessStep(id="step_1", title="Ingest & Normalize", description="Parse input topic or reference presentation tokens.", order=1),
            ProcessStep(id="step_2", title="Semantic Planning", description="Construct structured domain blueprint via AI orchestrator.", order=2),
            ProcessStep(id="step_3", title="Deterministic Layout", description="Compute 1920x1080 virtual coordinates and port geometry.", order=3),
            ProcessStep(id="step_4", title="Native PPTX Render", description="Emit fully editable PowerPoint package with zero rasterization.", order=4),
        ]

        count = len(steps)
        card_rects = calculate_card_row(content_rect, count=count, gap=ctx.card_gap + 20)

        for i, rect in enumerate(card_rects):
            step = steps[i]
            step_id = f"{slide.id}_{step.id}"
            ports = generate_ports(step_id, rect)

            elements.append(
                ElementGeometry(
                    id=step_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="process_step",
                    importance="primary" if i == 0 else "secondary",
                    content_data={
                        "step_number": f"{i+1:02d}",
                        "title": step.title,
                        "description": step.description,
                    },
                )
            )

            # Add forward arrow connector between consecutive steps
            if i > 0:
                prev_id = f"{slide.id}_{steps[i-1].id}"
                prev_rect = card_rects[i-1]
                connectors.append(
                    ConnectorGeometry(
                        id=f"{slide.id}_arrow_{i}",
                        start_port_id=f"{prev_id}_port_right",
                        end_port_id=f"{step_id}_port_left",
                        start_x=prev_rect.right,
                        start_y=prev_rect.center_y,
                        end_x=rect.x,
                        end_y=rect.center_y,
                        connector_type="arrow",
                        stroke_width=3,
                    )
                )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 11. Flowchart Layout
# ---------------------------------------------------------------------------
class FlowchartResolver(BaseArchetypeResolver):
    """Workflow node diagram with decision, process, and terminal nodes with ports."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        # 3 horizontal stages: Start -> Process/Decision -> End
        node_w = round(content_rect.width * 0.26)
        node_h = round(content_rect.height * 0.45)
        gap_x = (content_rect.width - (3 * node_w)) // 2
        y_pos = content_rect.center_y - (node_h // 2)

        stages = [
            ("start_node", "Input Request", "Topic prompt or reference PPTX file", ElementType.SHAPE),
            ("process_node", "Layout Resolver", "Deterministic constraint solving & font fitting", ElementType.CARD),
            ("end_node", "Output PPTX", "Production-grade editable presentation", ElementType.SHAPE),
        ]

        for i, (sid, title, desc, etype) in enumerate(stages):
            node_x = content_rect.x + (i * (node_w + gap_x))
            rect = Rect(x=node_x, y=y_pos, width=node_w, height=node_h)
            node_id = f"{slide.id}_{sid}"
            ports = generate_ports(node_id, rect)

            elements.append(
                ElementGeometry(
                    id=node_id,
                    semantic_type=etype,
                    rect=rect,
                    alignment=Alignment.CENTER,
                    ports=ports,
                    role="flowchart_node",
                    importance="primary" if i == 1 else "secondary",
                    content_data={"title": title, "description": desc},
                )
            )

            if i > 0:
                prev_id = f"{slide.id}_{stages[i-1][0]}"
                prev_x = content_rect.x + ((i-1) * (node_w + gap_x)) + node_w
                connectors.append(
                    ConnectorGeometry(
                        id=f"{slide.id}_flow_conn_{i}",
                        start_port_id=f"{prev_id}_port_right",
                        end_port_id=f"{node_id}_port_left",
                        start_x=prev_x,
                        start_y=y_pos + (node_h // 2),
                        end_x=node_x,
                        end_y=y_pos + (node_h // 2),
                        connector_type="arrow",
                        stroke_width=3,
                    )
                )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 12. Hierarchy / Tree Layout
# ---------------------------------------------------------------------------
class HierarchyTreeResolver(BaseArchetypeResolver):
    """Multi-tier tree structure with parent-child hierarchical connectors."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        # Tier 0 (Root): Centered at top
        root_w = round(content_rect.width * 0.4)
        root_h = round(content_rect.height * 0.3)
        root_x = content_rect.center_x - (root_w // 2)
        root_rect = Rect(x=root_x, y=content_rect.y, width=root_w, height=root_h)
        root_id = f"{slide.id}_root_tier"

        elements.append(
            ElementGeometry(
                id=root_id,
                semantic_type=ElementType.CARD,
                rect=root_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(root_id, root_rect),
                role="tree_root",
                importance="primary",
                content_data={"title": "Root Controller", "description": "High-level domain orchestrator"},
            )
        )

        # Tier 1 (Children): 3 distributed child cards
        child_count = 3
        tier1_y = content_rect.y + root_h + ctx.row_gap + 40
        tier1_h = content_rect.bottom - tier1_y
        child_rects = calculate_card_row(
            Rect(x=content_rect.x, y=tier1_y, width=content_rect.width, height=tier1_h),
            count=child_count,
            gap=ctx.card_gap,
        )

        child_titles = ["AI Planning Subsystem", "Layout Resolution Engine", "OpenXML Shape Renderer"]

        for i, r in enumerate(child_rects):
            cid = f"{slide.id}_child_{i+1}"
            ports = generate_ports(cid, r)
            elements.append(
                ElementGeometry(
                    id=cid,
                    semantic_type=ElementType.CARD,
                    rect=r,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="tree_child",
                    importance="secondary",
                    content_data={"title": child_titles[i], "description": "Modular decoupled service node"},
                )
            )

            # Connector from root bottom to child top
            connectors.append(
                ConnectorGeometry(
                    id=f"{slide.id}_tree_conn_{i+1}",
                    start_port_id=f"{root_id}_port_bottom",
                    end_port_id=f"{cid}_port_top",
                    start_x=root_rect.center_x,
                    start_y=root_rect.bottom,
                    end_x=r.center_x,
                    end_y=r.y,
                    connector_type="arrow",
                    stroke_width=2,
                )
            )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 13. Architecture Diagram Layout
# ---------------------------------------------------------------------------
class ArchitectureResolver(BaseArchetypeResolver):
    """Layered architecture stacks with inter-layer connectors."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        layers = [
            ("layer_presentation", "Presentation & UI Layer", "React 19, Vite, Tailwind CSS v4, Lucide Icons"),
            ("layer_gateway", "API Gateway & Middleware Layer", "FastAPI, Correlation IDs, Structured Logging"),
            ("layer_engine", "Layout & Orchestration Engine", "Deterministic 1920x1080 constraint solver"),
            ("layer_render", "Native PPTX Rendering Layer", "python-pptx, OpenXML shapes, zero rasterization"),
        ]

        layer_slices = distribute_vertical(content_rect.height, count=len(layers), gap=ctx.row_gap)

        for i, (sid, title, subtitle) in enumerate(layers):
            offset_y, layer_h = layer_slices[i]
            rect = Rect(
                x=content_rect.x,
                y=content_rect.y + offset_y,
                width=content_rect.width,
                height=layer_h,
            )
            layer_id = f"{slide.id}_{sid}"
            ports = generate_ports(layer_id, rect)

            elements.append(
                ElementGeometry(
                    id=layer_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="architecture_layer",
                    importance="primary" if i == 2 else "secondary",
                    content_data={"title": title, "subtitle": subtitle},
                )
            )

            if i > 0:
                prev_id = f"{slide.id}_{layers[i-1][0]}"
                prev_y = content_rect.y + layer_slices[i-1][0] + layer_slices[i-1][1]
                connectors.append(
                    ConnectorGeometry(
                        id=f"{slide.id}_arch_conn_{i}",
                        start_port_id=f"{prev_id}_port_bottom",
                        end_port_id=f"{layer_id}_port_top",
                        start_x=content_rect.center_x,
                        start_y=prev_y,
                        end_x=content_rect.center_x,
                        end_y=rect.y,
                        connector_type="arrow",
                        stroke_width=2,
                    )
                )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 14. Matrix (2x2) Layout
# ---------------------------------------------------------------------------
class MatrixResolver(BaseArchetypeResolver):
    """2x2 quadrant matrix with X and Y axis labels and quadrant cards."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        # Axis label offsets
        axis_offset_x = 40
        axis_offset_y = 30
        grid_rect = Rect(
            x=content_rect.x + axis_offset_x,
            y=content_rect.y,
            width=content_rect.width - axis_offset_x,
            height=content_rect.height - axis_offset_y,
        )

        grid = calculate_grid(grid_rect, cols=2, rows=2, col_gap=ctx.column_gap, row_gap=ctx.row_gap)

        quadrants = [
            ("q1", "High Impact / Low Effort", "Quick Wins: Instant value delivery with low friction", "accent"),
            ("q2", "High Impact / High Effort", "Strategic Bets: Long-term architectural milestones", "primary"),
            ("q3", "Low Impact / Low Effort", "Incremental: Routine optimization & bug fixes", "secondary"),
            ("q4", "Low Impact / High Effort", "Deprioritized: Avoid high complexity low yield items", "secondary"),
        ]

        idx = 0
        for row in grid:
            for cell_rect in row:
                qid, title, desc, imp = quadrants[idx]
                quad_id = f"{slide.id}_{qid}"
                elements.append(
                    ElementGeometry(
                        id=quad_id,
                        semantic_type=ElementType.CARD,
                        rect=cell_rect,
                        alignment=Alignment.LEFT,
                        ports=generate_ports(quad_id, cell_rect),
                        role="quadrant",
                        importance=imp,
                        content_data={"title": title, "description": desc},
                    )
                )
                idx += 1

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 15. Table + Summary Layout
# ---------------------------------------------------------------------------
class TableSummaryResolver(BaseArchetypeResolver):
    """Native table container layout with optional side takeaway card."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        # 70% Table container + 30% Side Insight Summary
        left_w = round(content_rect.width * 0.70)
        right_w = content_rect.width - left_w - ctx.column_gap

        table_rect = Rect(x=content_rect.x, y=content_rect.y, width=left_w, height=content_rect.height)
        insight_rect = Rect(
            x=content_rect.x + left_w + ctx.column_gap,
            y=content_rect.y,
            width=right_w,
            height=content_rect.height,
        )

        table_id = f"{slide.id}_table_container"
        insight_id = f"{slide.id}_table_insight"

        elements.append(
            ElementGeometry(
                id=table_id,
                semantic_type=ElementType.TABLE,
                rect=table_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(table_id, table_rect),
                role="data_table",
                importance="primary",
                content_data=slide.visual_plan.table_data,
            )
        )

        elements.append(
            ElementGeometry(
                id=insight_id,
                semantic_type=ElementType.CARD,
                rect=insight_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(insight_id, insight_rect),
                role="insight_card",
                importance="secondary",
                content_data={
                    "title": "Key Takeaways",
                    "bullets": [
                        "Performance benchmarks exceed target SLA.",
                        "Direct OpenXML parity ensures clean rendering.",
                        "Scales across enterprise data matrices.",
                    ],
                },
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 16. Chart + Insight Layout
# ---------------------------------------------------------------------------
class ChartInsightResolver(BaseArchetypeResolver):
    """Chart container (65% width) + key takeaway insight card (35% width)."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        chart_w = round(content_rect.width * 0.65)
        insight_w = content_rect.width - chart_w - ctx.column_gap

        chart_rect = Rect(x=content_rect.x, y=content_rect.y, width=chart_w, height=content_rect.height)
        insight_rect = Rect(
            x=content_rect.x + chart_w + ctx.column_gap,
            y=content_rect.y,
            width=insight_w,
            height=content_rect.height,
        )

        chart_id = f"{slide.id}_chart_container"
        insight_id = f"{slide.id}_chart_insight"

        elements.append(
            ElementGeometry(
                id=chart_id,
                semantic_type=ElementType.CHART,
                rect=chart_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(chart_id, chart_rect),
                role="chart_display",
                importance="primary",
                content_data=slide.visual_plan.chart_data,
            )
        )

        elements.append(
            ElementGeometry(
                id=insight_id,
                semantic_type=ElementType.CARD,
                rect=insight_rect,
                alignment=Alignment.LEFT,
                ports=generate_ports(insight_id, insight_rect),
                role="insight_panel",
                importance="secondary",
                content_data={
                    "title": "Data Insights",
                    "body": "Empirical evaluation demonstrates accelerated velocity and robust constraint adherence across all presentation batches.",
                },
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 17. Quote Layout
# ---------------------------------------------------------------------------
class QuoteResolver(BaseArchetypeResolver):
    """Prominent quotation layout with large typography and attribution card."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        card_w = round(content_rect.width * 0.85)
        card_h = round(content_rect.height * 0.75)
        card_x = content_rect.center_x - (card_w // 2)
        card_y = content_rect.center_y - (card_h // 2)

        card_rect = Rect(x=card_x, y=card_y, width=card_w, height=card_h)
        quote_id = f"{slide.id}_quote_card"

        quote_text = slide.purpose or (slide.elements[0].text_content.text if slide.elements and slide.elements[0].text_content else "Simplicity is the prerequisite for reliability.")
        author = slide.subtitle or "System Architect"

        elements.append(
            ElementGeometry(
                id=quote_id,
                semantic_type=ElementType.CARD,
                rect=card_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(quote_id, card_rect),
                role="quote",
                importance="primary",
                style_hints={"variant": "quote_box", "decorative_glyph": True},
                content_data={"quote": quote_text, "author": author},
            )
        )

        return elements, [], warnings


# ---------------------------------------------------------------------------
# 18. Roadmap Layout
# ---------------------------------------------------------------------------
class RoadmapResolver(BaseArchetypeResolver):
    """Multi-horizon strategic roadmap with phase swimlanes and deliverable cards."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        warnings: list[LayoutWarning] = []

        horizons = [
            ("Horizon 1 (Now)", "Near-Term Priorities", ["Deterministic Layout Engine", "Native PPTX Renderer"]),
            ("Horizon 2 (Next)", "Mid-Term Capabilities", ["Reference PPT Analyzer", "Semantic Visual Selector"]),
            ("Horizon 3 (Later)", "Long-Term Expansion", ["Visual QA 3-Pass Auto-Correction", "Enterprise Job Delivery"]),
        ]

        lane_rects = calculate_card_row(content_rect, count=len(horizons), gap=ctx.card_gap)

        for i, rect in enumerate(lane_rects):
            h_title, h_sub, deliverables = horizons[i]
            lane_id = f"{slide.id}_roadmap_lane_{i+1}"
            ports = generate_ports(lane_id, rect)

            elements.append(
                ElementGeometry(
                    id=lane_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="roadmap_horizon",
                    importance="primary" if i == 0 else "secondary",
                    content_data={
                        "phase": h_title,
                        "theme": h_sub,
                        "deliverables": deliverables,
                    },
                )
            )

        return elements, [], warnings
