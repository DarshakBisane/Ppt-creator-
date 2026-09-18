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
    calculate_multi_row_cards,
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
            card_rects = calculate_multi_row_cards(content_rect, count=count, max_cols=4, col_gap=ctx.card_gap, row_gap=ctx.row_gap)
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

        count = len(slide.elements) if 1 <= len(slide.elements) <= 3 else 3
        card_rects = calculate_card_row(content_rect, count=count, gap=ctx.card_gap)

        default_cards = [
            {"title": "Core Architecture", "body": "Fundamental operational principles and system infrastructure.", "icon": "Layers"},
            {"title": "Validation & Security", "body": "Strict protocol compliance and automated verification controls.", "icon": "Shield"},
            {"title": "Scalable Execution", "body": "High-throughput operational workflows with robust fault tolerance.", "icon": "Workflow"},
        ]

        for i, rect in enumerate(card_rects):
            elem = slide.elements[i] if i < len(slide.elements) else None
            card_id = elem.id if elem else f"{slide.id}_card_{i+1}"
            content = elem.card_content.model_dump() if elem and elem.card_content else default_cards[i % len(default_cards)]

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
            {"title": "Structural Foundations", "body": "Core domain architecture and protocol specifications."},
            {"title": "Workflow Processing", "body": "Automated end-to-end execution and lifecycle management."},
            {"title": "Security Boundaries", "body": "Multi-tier validation, cryptographic trust, and access control."},
            {"title": "Operational Governance", "body": "Continuous auditing, telemetry metrics, and SLA enforcement."},
        ]

        for i, rect in enumerate(flat_rects):
            elem = slide.elements[i] if i < len(slide.elements) else None
            card_id = elem.id if elem else f"{slide.id}_grid_card_{i+1}"
            content = elem.card_content.model_dump() if elem and elem.card_content else default_items[i % len(default_items)]

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
            {"value": "99.99%", "unit": "Availability", "label": "Operational Uptime", "trend": "up", "context": "Target benchmark achieved"},
            {"value": "<10ms", "unit": "Latency", "label": "Verification Speed", "trend": "up", "context": "Sub-second real-time response"},
            {"value": "100%", "unit": "Verified", "label": "Integrity Compliance", "trend": "neutral", "context": "Zero security deviations"},
            {"value": "4.9/5", "unit": "Rating", "label": "System Confidence", "trend": "up", "context": "Audited by governance standards"},
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

        if slide.visual_plan.table_data and len(slide.visual_plan.table_data.columns) >= 3:
            td = slide.visual_plan.table_data
            l_col = td.columns[1].label
            r_col = td.columns[2].label
            l_pts = [f"{r.cells[0]}: {r.cells[1]}" for r in td.rows if len(r.cells) >= 2]
            r_pts = [f"{r.cells[0]}: {r.cells[2]}" for r in td.rows if len(r.cells) >= 3]
            left_data = {"title": l_col, "points": l_pts}
            right_data = {"title": r_col, "points": r_pts}
        elif len(slide.elements) >= 2:
            e1 = slide.elements[0]
            e2 = slide.elements[1]
            left_data = {
                "title": e1.card_content.title if e1.card_content else "Option A / Baseline",
                "points": [e1.card_content.body] if e1.card_content else ["Standard operational baseline."],
            }
            right_data = {
                "title": e2.card_content.title if e2.card_content else "Option B / Proposed",
                "points": [e2.card_content.body] if e2.card_content else ["Target architecture with enhanced scalability."],
            }
        else:
            left_data = {
                "title": "Traditional / Baseline",
                "points": [
                    "Manual execution and verification bottlenecks",
                    "Fragmented architecture and limited visibility",
                    "Higher operational latency and failure risk",
                ],
            }
            right_data = {
                "title": "Target Architecture",
                "points": [
                    "Automated end-to-end workflow execution",
                    "Decentralized trust and unified verification",
                    "High throughput with robust fault tolerance",
                ],
            }

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
                content_data=left_data,
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
                content_data=right_data,
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
            TimelineMilestone(label="Phase 1", date="Milestone 1", description="Architecture & Requirements Definition", status=TimelineStatus.COMPLETED),
            TimelineMilestone(label="Phase 2", date="Milestone 2", description="Core Implementation & Protocol Integration", status=TimelineStatus.CURRENT),
            TimelineMilestone(label="Phase 3", date="Milestone 3", description="System Verification & Security Validation", status=TimelineStatus.PLANNED),
            TimelineMilestone(label="Phase 4", date="Milestone 4", description="Production Deployment & Monitoring", status=TimelineStatus.PLANNED),
        ]

        count = min(len(milestones), 4)
        active_milestones = milestones[:count]

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
            m = active_milestones[i]
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
        if pf_data and pf_data.steps:
            steps = pf_data.steps
        elif slide.elements:
            steps = [
                ProcessStep(
                    id=f"step_{i+1}",
                    title=elem.card_content.title if elem.card_content else f"Step {i+1}",
                    description=elem.card_content.body if elem.card_content else "",
                    order=i+1,
                )
                for i, elem in enumerate(slide.elements)
            ]
        else:
            steps = [
                ProcessStep(id="step_1", title="Initialization & Request", description="User or client generates secure request with verified identity.", order=1),
                ProcessStep(id="step_2", title="Verification & Policy", description="Authority validates request parameters and policy compliance.", order=2),
                ProcessStep(id="step_3", title="Execution & Issuance", description="Core system processes payload and generates signed artifact.", order=3),
                ProcessStep(id="step_4", title="Deployment & Usage", description="Target repository stores artifact for operational usage.", order=4),
            ]

        count = len(steps)
        card_rects = calculate_multi_row_cards(content_rect, count=count, max_cols=4, col_gap=ctx.card_gap + 10, row_gap=ctx.row_gap + 10)

        for i, (rect, step) in enumerate(zip(card_rects, steps)):
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
                
                if abs(rect.y - prev_rect.y) < 20:
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
                else:
                    connectors.append(
                        ConnectorGeometry(
                            id=f"{slide.id}_turnaround_{i}",
                            start_port_id=f"{prev_id}_port_bottom",
                            end_port_id=f"{step_id}_port_top",
                            start_x=prev_rect.center_x,
                            start_y=prev_rect.bottom,
                            end_x=rect.center_x,
                            end_y=rect.y,
                            connector_type="arrow",
                            stroke_width=2,
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

        if slide.elements and len(slide.elements) >= 3:
            stages = [
                (elem.id, elem.card_content.title if elem.card_content else f"Stage {i+1}",
                 elem.card_content.body if elem.card_content else "",
                 ElementType.CARD if i == 1 else ElementType.SHAPE)
                for i, elem in enumerate(slide.elements[:3])
            ]
        else:
            stages = [
                ("start_node", "Input & Authentication", "Client initiates secure request payload", ElementType.SHAPE),
                ("process_node", "Core Verification Engine", "Validation of cryptographic signatures and policy", ElementType.CARD),
                ("end_node", "Verified Output", "Authorized operation and secure artifact delivery", ElementType.SHAPE),
            ]

        node_w = round(content_rect.width * 0.26)
        node_h = round(content_rect.height * 0.45)
        gap_x = (content_rect.width - (len(stages) * node_w)) // max(1, len(stages) - 1)
        y_pos = content_rect.center_y - (node_h // 2)

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
        root_w = round(content_rect.width * 0.44)
        root_h = round(content_rect.height * 0.28)
        root_x = content_rect.center_x - (root_w // 2)
        root_rect = Rect(x=root_x, y=content_rect.y, width=root_w, height=root_h)
        root_id = f"{slide.id}_root_tier"

        root_title = slide.title.split(":")[0][:40]
        elements.append(
            ElementGeometry(
                id=root_id,
                semantic_type=ElementType.CARD,
                rect=root_rect,
                alignment=Alignment.CENTER,
                ports=generate_ports(root_id, root_rect),
                role="tree_root",
                importance="primary",
                content_data={"title": root_title, "description": slide.purpose or "Primary domain root anchor and authority controller"},
            )
        )

        if slide.elements:
            child_items = [
                (elem.card_content.title if elem.card_content else f"Component {i+1}",
                 elem.card_content.body if elem.card_content else "Domain architectural subsystem")
                for i, elem in enumerate(slide.elements[:3])
            ]
        else:
            child_items = [
                ("Primary Service Controller", "High-level domain logic and workflow coordination"),
                ("Processing & Validation Engine", "Automated cryptographic verification and policy enforcement"),
                ("Storage & Audit Repository", "Persistent state management and compliance records"),
            ]

        child_count = len(child_items)
        tier1_y = content_rect.y + root_h + ctx.row_gap + 30
        tier1_h = content_rect.bottom - tier1_y
        child_rects = calculate_card_row(
            Rect(x=content_rect.x, y=tier1_y, width=content_rect.width, height=tier1_h),
            count=child_count,
            gap=ctx.card_gap,
        )

        for i, (c_title, c_desc) in enumerate(child_items):
            r = child_rects[i]
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
                    content_data={"title": c_title, "description": c_desc},
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

        if slide.elements and len(slide.elements) >= 2:
            layers = [
                (elem.id,
                 elem.card_content.title if elem.card_content else f"Layer {i+1}",
                 elem.card_content.body if elem.card_content else "Subsystem architecture tier and protocol boundary")
                for i, elem in enumerate(slide.elements[:4])
            ]
        else:
            layers = [
                (f"{slide.id}_layer_client", "User & Client Application Layer", "Request submission, credential management, and interactive client UI"),
                (f"{slide.id}_layer_gateway", "Security & Validation Gateway", "Authentication, request routing, and policy verification"),
                (f"{slide.id}_layer_core", "Core Authority & Processing Engine", "Digital signature generation, lifecycle transitions, and business logic"),
                (f"{slide.id}_layer_repository", "Storage, Repository & Revocation", "Certificate registry, CRL/OCSP store, and secure audit logging"),
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
            layer_id = f"{slide.id}_arch_{i+1}"
            ports = generate_ports(layer_id, rect)

            elements.append(
                ElementGeometry(
                    id=layer_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="architecture_layer",
                    importance="primary" if i == (len(layers) // 2) else "secondary",
                    content_data={"title": title, "subtitle": subtitle},
                )
            )

            if i > 0:
                prev_id = f"{slide.id}_arch_{i}"
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

        takeaways = [
            elem.text_content.text if elem.text_content else (elem.card_content.title if elem.card_content else elem.role)
            for elem in slide.elements
        ] if slide.elements else [
            slide.purpose or "Key structured findings and domain metrics.",
            "Structured comparison across operational dimensions.",
            "Verified against domain baseline benchmarks.",
        ]

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
                    "bullets": takeaways[:4],
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

        insight_text = slide.purpose or (
            slide.elements[0].card_content.body if slide.elements and slide.elements[0].card_content else
            "Empirical evaluation demonstrates measurable progress across key domain performance metrics."
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
                    "body": insight_text,
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
        author = slide.subtitle or "Domain Specialist"

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

        if slide.elements and len(slide.elements) >= 2:
            horizons = [
                (elem.card_content.title if elem.card_content else f"Phase {i+1}",
                 elem.card_content.supporting_text if elem.card_content and elem.card_content.supporting_text else f"Horizon {i+1}",
                 [elem.card_content.body] if elem.card_content and elem.card_content.body else ["Key milestone execution", "Deliverable verification"])
                for i, elem in enumerate(slide.elements[:4])
            ]
        else:
            horizons = [
                ("Horizon 1: Foundation", "Near-Term Priorities", ["Initial scoping & requirements", "Core architecture baseline"]),
                ("Horizon 2: Execution", "Mid-Term Capabilities", ["System integration & rollout", "Validation & performance tuning"]),
                ("Horizon 3: Expansion", "Long-Term Strategic Scale", ["Operational scaling & automation", "Continuous governance & monitoring"]),
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


# ---------------------------------------------------------------------------
# 19. Anatomy Diagram Layout
# ---------------------------------------------------------------------------
class AnatomyResolver(BaseArchetypeResolver):
    """Central structural object with labeled callout components and connector lines."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        # Center core block width & height
        center_w = round(content_rect.width * 0.36)
        center_h = round(content_rect.height * 0.70)
        center_x = content_rect.x + (content_rect.width - center_w) // 2
        center_y = content_rect.y + (content_rect.height - center_h) // 2

        center_rect = Rect(x=center_x, y=center_y, width=center_w, height=center_h)
        center_id = f"{slide.id}_anatomy_core"
        center_ports = generate_ports(center_id, center_rect)

        core_title = slide.title.split(":")[0][:40]
        elements.append(
            ElementGeometry(
                id=center_id,
                semantic_type=ElementType.CARD,
                rect=center_rect,
                alignment=Alignment.CENTER,
                ports=center_ports,
                role="anatomy_core",
                importance="primary",
                style_hints={"variant": "hero_banner", "accent_border": True},
                content_data={
                    "title": core_title,
                    "body": slide.purpose or "Core structural specification, attributes, and key parameters.",
                },
            )
        )

        # Callout items (left and right columns)
        callout_items = [
            (elem.card_content.title if elem.card_content else f"Component {i+1}",
             elem.card_content.body if elem.card_content else "Functional attribute and operational role.")
            for i, elem in enumerate(slide.elements)
        ]
        if not callout_items:
            callout_items = [
                ("Primary Identifier & Metadata", "Unique identification, serial numbering, and descriptive scope."),
                ("Identity & Authority Bindings", "Entity attributes and authenticated relationship parameters."),
                ("Core Parameters & Attributes", "Underlying specifications, operational limits, and settings."),
                ("Validation & Status Integrity", "Integrity guarantees, verification status, and audit trail."),
            ]

        left_items = callout_items[:(len(callout_items) + 1) // 2]
        right_items = callout_items[(len(callout_items) + 1) // 2:]

        callout_w = (center_x - content_rect.x) - ctx.column_gap

        # Left Column Callouts
        if left_items:
            left_h = (content_rect.height - (ctx.row_gap * (len(left_items) - 1))) // len(left_items)
            for i, (c_title, c_desc) in enumerate(left_items):
                c_rect = Rect(
                    x=content_rect.x,
                    y=content_rect.y + i * (left_h + ctx.row_gap),
                    width=callout_w,
                    height=left_h,
                )
                c_id = f"{slide.id}_callout_left_{i+1}"
                c_ports = generate_ports(c_id, c_rect)
                elements.append(
                    ElementGeometry(
                        id=c_id,
                        semantic_type=ElementType.CARD,
                        rect=c_rect,
                        alignment=Alignment.LEFT,
                        ports=c_ports,
                        role="callout",
                        importance="secondary",
                        content_data={"title": c_title, "body": c_desc},
                    )
                )
                # Connector to center core
                connectors.append(
                    ConnectorGeometry(
                        id=f"conn_left_{i+1}",
                        start_port_id=f"{c_id}_port_right",
                        end_port_id=f"{center_id}_port_left",
                        start_x=c_rect.right,
                        start_y=c_rect.center_y,
                        end_x=center_rect.x,
                        end_y=c_rect.center_y,
                        connector_type="line",
                        stroke_width=2,
                    )
                )

        # Right Column Callouts
        if right_items:
            right_h = (content_rect.height - (ctx.row_gap * (len(right_items) - 1))) // len(right_items)
            right_x = center_rect.right + ctx.column_gap
            for i, (c_title, c_desc) in enumerate(right_items):
                c_rect = Rect(
                    x=right_x,
                    y=content_rect.y + i * (right_h + ctx.row_gap),
                    width=callout_w,
                    height=right_h,
                )
                c_id = f"{slide.id}_callout_right_{i+1}"
                c_ports = generate_ports(c_id, c_rect)
                elements.append(
                    ElementGeometry(
                        id=c_id,
                        semantic_type=ElementType.CARD,
                        rect=c_rect,
                        alignment=Alignment.LEFT,
                        ports=c_ports,
                        role="callout",
                        importance="secondary",
                        content_data={"title": c_title, "body": c_desc},
                    )
                )
                # Connector to center core
                connectors.append(
                    ConnectorGeometry(
                        id=f"conn_right_{i+1}",
                        start_port_id=f"{center_id}_port_right",
                        end_port_id=f"{c_id}_port_left",
                        start_x=center_rect.right,
                        start_y=c_rect.center_y,
                        end_x=c_rect.x,
                        end_y=c_rect.center_y,
                        connector_type="line",
                        stroke_width=2,
                    )
                )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 20. Lifecycle Flow Layout
# ---------------------------------------------------------------------------
class LifecycleResolver(BaseArchetypeResolver):
    """End-to-end progression with sequential step nodes and transition arrows, supporting multi-row layouts."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        stages = [
            (elem.card_content.title if elem.card_content else f"Stage {i+1}",
             elem.card_content.body if elem.card_content else "")
            for i, elem in enumerate(slide.elements)
        ]
        if not stages:
            stages = [
                ("Stage 1: Ingestion & Planning", "Initial requirement definition, entity registration, and parameter configuration."),
                ("Stage 2: Validation & Review", "Policy verification, prerequisite validation, and authorization approval."),
                ("Stage 3: Execution & Issuance", "Core entity generation, cryptographic signing, and operational deployment."),
                ("Stage 4: Monitoring & Renewal", "Continuous telemetry inspection, lifecycle health tracking, and scheduled maintenance."),
            ]

        count = len(stages)
        # Content-aware multi-row calculation: clamp max columns to 4
        if count <= 4:
            card_rects = calculate_card_row(content_rect, count=count, gap=ctx.card_gap)
            cols_per_row = count
        else:
            card_rects = calculate_multi_row_cards(content_rect, count=count, max_cols=4, col_gap=ctx.card_gap, row_gap=ctx.row_gap)
            cols_per_row = min(4, (count + 1) // 2)

        for i, (rect, (s_title, s_desc)) in enumerate(zip(card_rects, stages)):
            node_id = f"{slide.id}_lifecycle_node_{i+1}"
            ports = generate_ports(node_id, rect)

            step_label = f"0{i+1}" if i < 9 else str(i+1)
            elements.append(
                ElementGeometry(
                    id=node_id,
                    semantic_type=ElementType.CARD,
                    rect=rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="process_step",
                    importance="primary" if i == 0 else "secondary",
                    style_hints={"variant": "lifecycle_card", "step_num": step_label},
                    content_data={"title": s_title, "body": s_desc},
                )
            )

            if i > 0:
                prev_rect = card_rects[i - 1]
                prev_id = f"{slide.id}_lifecycle_node_{i}"

                # Determine if this step starts a new row
                is_row_transition = (i % cols_per_row == 0) and (count > 4)

                if is_row_transition:
                    # Turnaround connector from previous row end (bottom) to current row start (top)
                    connectors.append(
                        ConnectorGeometry(
                            id=f"conn_lifecycle_{i}",
                            start_port_id=f"{prev_id}_port_bottom",
                            end_port_id=f"{node_id}_port_top",
                            start_x=prev_rect.center_x,
                            start_y=prev_rect.bottom,
                            end_x=rect.center_x,
                            end_y=rect.y,
                            connector_type="arrow",
                            stroke_width=2,
                        )
                    )
                else:
                    # Standard horizontal arrow (left to right)
                    connectors.append(
                        ConnectorGeometry(
                            id=f"conn_lifecycle_{i}",
                            start_port_id=f"{prev_id}_port_right",
                            end_port_id=f"{node_id}_port_left",
                            start_x=prev_rect.right,
                            start_y=prev_rect.center_y,
                            end_x=rect.x,
                            end_y=rect.center_y,
                            connector_type="arrow",
                            stroke_width=2,
                        )
                    )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 21. Decision Flow Layout
# ---------------------------------------------------------------------------
class DecisionFlowResolver(BaseArchetypeResolver):
    """Step-by-step verification pipeline with decision checkpoints and final verdict node."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        checkpoints = [
            (elem.card_content.title if elem.card_content else f"Check {i+1}",
             elem.card_content.body if elem.card_content else "Validation rule applied against system policy.")
            for i, elem in enumerate(slide.elements)
        ]
        if not checkpoints:
            checkpoints = [
                ("1. Input Ingestion", "System receives incoming request parameters and payload."),
                ("2. Policy Verification", "Verify parameters against enterprise compliance and authorization policies."),
                ("3. Signature & Integrity Check", "Validate cryptographic signature and message integrity."),
                ("4. Real-Time Status Verification", "Query active directory / revocation repository for live status."),
            ]

        # Left column: checkpoints (68% width); Right column: verdict badge (32% width)
        left_w = round(content_rect.width * 0.68)
        right_w = content_rect.width - left_w - ctx.column_gap

        step_h = (content_rect.height - (ctx.row_gap * (len(checkpoints) - 1))) // len(checkpoints)
        check_rects: list[Rect] = []

        for i, (c_title, c_desc) in enumerate(checkpoints):
            c_rect = Rect(
                x=content_rect.x,
                y=content_rect.y + i * (step_h + ctx.row_gap),
                width=left_w,
                height=step_h,
            )
            check_rects.append(c_rect)
            c_id = f"{slide.id}_checkpoint_{i+1}"
            ports = generate_ports(c_id, c_rect)

            elements.append(
                ElementGeometry(
                    id=c_id,
                    semantic_type=ElementType.CARD,
                    rect=c_rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="decision_step",
                    importance="secondary",
                    style_hints={"variant": "decision_step"},
                    content_data={"title": c_title, "body": c_desc},
                )
            )

            if i > 0:
                prev_c_rect = check_rects[i - 1]
                prev_id = f"{slide.id}_checkpoint_{i}"
                connectors.append(
                    ConnectorGeometry(
                        id=f"conn_check_{i}",
                        start_port_id=f"{prev_id}_port_bottom",
                        end_port_id=f"{c_id}_port_top",
                        start_x=prev_c_rect.center_x,
                        start_y=prev_c_rect.bottom,
                        end_x=c_rect.center_x,
                        end_y=c_rect.y,
                        connector_type="arrow",
                        stroke_width=2,
                    )
                )

        # Right Column: Verdict / Trust Confirmation Card
        verdict_rect = Rect(
            x=content_rect.x + left_w + ctx.column_gap,
            y=content_rect.y,
            width=right_w,
            height=content_rect.height,
        )
        verdict_id = f"{slide.id}_verdict_card"
        v_ports = generate_ports(verdict_id, verdict_rect)

        verdict_title = "VERIFIED & APPROVED"
        verdict_body = slide.purpose or "All validation checkpoints, integrity policies, and compliance rules successfully verified."

        elements.append(
            ElementGeometry(
                id=verdict_id,
                semantic_type=ElementType.CARD,
                rect=verdict_rect,
                alignment=Alignment.CENTER,
                ports=v_ports,
                role="verdict",
                importance="primary",
                style_hints={"variant": "hero_banner", "accent_border": True},
                content_data={
                    "title": verdict_title,
                    "body": verdict_body,
                },
            )
        )

        # Connector from last checkpoint to verdict card
        last_check_id = f"{slide.id}_checkpoint_{len(checkpoints)}"
        last_r = check_rects[-1]
        connectors.append(
            ConnectorGeometry(
                id="conn_to_verdict",
                start_port_id=f"{last_check_id}_port_right",
                end_port_id=f"{verdict_id}_port_left",
                start_x=last_r.right,
                start_y=last_r.center_y,
                end_x=verdict_rect.x,
                end_y=last_r.center_y,
                connector_type="arrow",
                stroke_width=2,
            )
        )

        return elements, connectors, warnings


# ---------------------------------------------------------------------------
# 22. Layered Stack Architecture Layout
# ---------------------------------------------------------------------------
class LayeredStackResolver(BaseArchetypeResolver):
    """Stacked hierarchical system architecture layers with layer badges and protocol annotations."""

    def resolve(
        self,
        slide: Slide,
        content_rect: Rect,
        ctx: SpacingContext,
    ) -> tuple[list[ElementGeometry], list[ConnectorGeometry], list[LayoutWarning]]:
        elements: list[ElementGeometry] = []
        connectors: list[ConnectorGeometry] = []
        warnings: list[LayoutWarning] = []

        if slide.elements and len(slide.elements) >= 2:
            layers = [
                (elem.card_content.title if elem.card_content else f"Tier {i+1}",
                 elem.card_content.body if elem.card_content else "Architecture layer components and protocol integration.")
                for i, elem in enumerate(slide.elements[:4])
            ]
        else:
            layers = [
                ("Application & Client Interface Layer", "User access points, client applications, and API consumption endpoints."),
                ("Service Gateway & Orchestration Layer", "Traffic routing, rate limiting, and business workflow coordination."),
                ("Core Processing & Logic Engine", "Domain rule execution, transactional processing, and cryptographic functions."),
                ("Data Persistence & Storage Layer", "Secure relational storage, caching layer, and audit event repository."),
            ]

        count = len(layers)
        layer_h = (content_rect.height - (ctx.row_gap * (count - 1))) // count
        layer_rects: list[Rect] = []

        for i, (l_title, l_desc) in enumerate(layers):
            l_rect = Rect(
                x=content_rect.x,
                y=content_rect.y + i * (layer_h + ctx.row_gap),
                width=content_rect.width,
                height=layer_h,
            )
            layer_rects.append(l_rect)
            l_id = f"{slide.id}_layer_{i+1}"
            ports = generate_ports(l_id, l_rect)

            elements.append(
                ElementGeometry(
                    id=l_id,
                    semantic_type=ElementType.CARD,
                    rect=l_rect,
                    alignment=Alignment.LEFT,
                    ports=ports,
                    role="architecture_layer",
                    importance="primary" if i == 0 else "secondary",
                    style_hints={"variant": "layer_card", "tier_num": f"L{count - i}"},
                    content_data={"title": f"LAYER {count - i}: {l_title.upper()}", "body": l_desc},
                )
            )

            if i > 0:
                prev_l_rect = layer_rects[i - 1]
                prev_id = f"{slide.id}_layer_{i}"
                connectors.append(
                    ConnectorGeometry(
                        id=f"conn_layer_{i}",
                        start_port_id=f"{prev_id}_port_bottom",
                        end_port_id=f"{l_id}_port_top",
                        start_x=content_rect.center_x,
                        start_y=prev_l_rect.bottom,
                        end_x=content_rect.center_x,
                        end_y=l_rect.y,
                        connector_type="arrow",
                        stroke_width=2,
                    )
                )

        return elements, connectors, warnings


