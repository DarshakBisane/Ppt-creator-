"""Canonical mapping between Phase 3 VisualType and Phase 6 layout archetypes."""

from pydantic import BaseModel
from backend.app.domain.enums import VisualType


class ArchetypeDescriptor(BaseModel):
    """Metadata and fallback definitions for a VisualType to layout archetype pairing."""

    visual_type: VisualType
    preferred_archetype: str
    fallback_archetype: str
    fallback_visual_type: VisualType
    requires_quantitative_data: bool = False
    min_items: int = 1
    max_items: int = 12
    description: str = ""


ARCHETYPE_MAPPINGS: dict[VisualType, ArchetypeDescriptor] = {
    VisualType.HERO: ArchetypeDescriptor(
        visual_type=VisualType.HERO,
        preferred_archetype="hero",
        fallback_archetype="title_body",
        fallback_visual_type=VisualType.TEXT,
        min_items=1,
        max_items=3,
        description="High-impact lead statement or prominent mission callout",
    ),
    VisualType.KPI: ArchetypeDescriptor(
        visual_type=VisualType.KPI,
        preferred_archetype="kpi_dashboard",
        fallback_archetype="three_card_row",
        fallback_visual_type=VisualType.CARD_GRID,
        requires_quantitative_data=True,
        min_items=2,
        max_items=4,
        description="Executive metric scorecards with large numbers and delta trends",
    ),
    VisualType.COMPARISON: ArchetypeDescriptor(
        visual_type=VisualType.COMPARISON,
        preferred_archetype="comparison",
        fallback_archetype="two_column",
        fallback_visual_type=VisualType.CARD_GRID,
        min_items=2,
        max_items=2,
        description="Side-by-side comparative panels with central VS divider",
    ),
    VisualType.TABLE: ArchetypeDescriptor(
        visual_type=VisualType.TABLE,
        preferred_archetype="table_summary",
        fallback_archetype="four_card_grid",
        fallback_visual_type=VisualType.CARD_GRID,
        min_items=2,
        max_items=8,
        description="Structured native table with columns and side takeaway callout",
    ),
    VisualType.BAR_CHART: ArchetypeDescriptor(
        visual_type=VisualType.BAR_CHART,
        preferred_archetype="chart_insight",
        fallback_archetype="kpi_dashboard",
        fallback_visual_type=VisualType.KPI,
        requires_quantitative_data=True,
        min_items=2,
        max_items=10,
        description="Horizontal bar chart for multi-category ranking",
    ),
    VisualType.COLUMN_CHART: ArchetypeDescriptor(
        visual_type=VisualType.COLUMN_CHART,
        preferred_archetype="chart_insight",
        fallback_archetype="kpi_dashboard",
        fallback_visual_type=VisualType.KPI,
        requires_quantitative_data=True,
        min_items=2,
        max_items=8,
        description="Vertical column chart for discrete categorical metrics",
    ),
    VisualType.LINE_CHART: ArchetypeDescriptor(
        visual_type=VisualType.LINE_CHART,
        preferred_archetype="chart_insight",
        fallback_archetype="timeline",
        fallback_visual_type=VisualType.TIMELINE,
        requires_quantitative_data=True,
        min_items=2,
        max_items=12,
        description="Continuous time-series trend progression",
    ),
    VisualType.PIE_CHART: ArchetypeDescriptor(
        visual_type=VisualType.PIE_CHART,
        preferred_archetype="chart_insight",
        fallback_archetype="kpi_dashboard",
        fallback_visual_type=VisualType.KPI,
        requires_quantitative_data=True,
        min_items=2,
        max_items=6,
        description="Part-to-whole proportional composition",
    ),
    VisualType.DONUT_CHART: ArchetypeDescriptor(
        visual_type=VisualType.DONUT_CHART,
        preferred_archetype="chart_insight",
        fallback_archetype="kpi_dashboard",
        fallback_visual_type=VisualType.KPI,
        requires_quantitative_data=True,
        min_items=2,
        max_items=6,
        description="Donut composition with central metric summary",
    ),
    VisualType.TIMELINE: ArchetypeDescriptor(
        visual_type=VisualType.TIMELINE,
        preferred_archetype="timeline",
        fallback_archetype="process_flow",
        fallback_visual_type=VisualType.PROCESS_FLOW,
        min_items=2,
        max_items=6,
        description="Horizontal milestone spine with dates and milestone nodes",
    ),
    VisualType.PROCESS_FLOW: ArchetypeDescriptor(
        visual_type=VisualType.PROCESS_FLOW,
        preferred_archetype="process_flow",
        fallback_archetype="three_card_row",
        fallback_visual_type=VisualType.CARD_GRID,
        min_items=2,
        max_items=5,
        description="Sequential workflow step cards with forward connectors",
    ),
    VisualType.FLOWCHART: ArchetypeDescriptor(
        visual_type=VisualType.FLOWCHART,
        preferred_archetype="flowchart",
        fallback_archetype="process_flow",
        fallback_visual_type=VisualType.PROCESS_FLOW,
        min_items=3,
        max_items=6,
        description="Input -> Decision / Process -> Output workflow diagram",
    ),
    VisualType.DIAGRAM: ArchetypeDescriptor(
        visual_type=VisualType.DIAGRAM,
        preferred_archetype="flowchart",
        fallback_archetype="four_card_grid",
        fallback_visual_type=VisualType.CARD_GRID,
        min_items=3,
        max_items=6,
        description="Structured visual system diagram",
    ),
    VisualType.HIERARCHY: ArchetypeDescriptor(
        visual_type=VisualType.HIERARCHY,
        preferred_archetype="hierarchy_tree",
        fallback_archetype="architecture",
        fallback_visual_type=VisualType.ARCHITECTURE,
        min_items=3,
        max_items=6,
        description="Root node to child tiers organizational hierarchy tree",
    ),
    VisualType.TREE: ArchetypeDescriptor(
        visual_type=VisualType.TREE,
        preferred_archetype="hierarchy_tree",
        fallback_archetype="architecture",
        fallback_visual_type=VisualType.ARCHITECTURE,
        min_items=3,
        max_items=6,
        description="Hierarchical tree decomposition",
    ),
    VisualType.ARCHITECTURE: ArchetypeDescriptor(
        visual_type=VisualType.ARCHITECTURE,
        preferred_archetype="architecture",
        fallback_archetype="flowchart",
        fallback_visual_type=VisualType.FLOWCHART,
        min_items=3,
        max_items=4,
        description="Multi-layer vertical stack with downward connection ports",
    ),
    VisualType.MATRIX: ArchetypeDescriptor(
        visual_type=VisualType.MATRIX,
        preferred_archetype="matrix",
        fallback_archetype="four_card_grid",
        fallback_visual_type=VisualType.CARD_GRID,
        min_items=4,
        max_items=4,
        description="2x2 strategic quadrant matrix with X and Y axis labels",
    ),
    VisualType.ROADMAP: ArchetypeDescriptor(
        visual_type=VisualType.ROADMAP,
        preferred_archetype="roadmap",
        fallback_archetype="timeline",
        fallback_visual_type=VisualType.TIMELINE,
        min_items=2,
        max_items=4,
        description="Multi-horizon strategic swimlanes across phases",
    ),
    VisualType.CYCLE: ArchetypeDescriptor(
        visual_type=VisualType.CYCLE,
        preferred_archetype="roadmap",
        fallback_archetype="process_flow",
        fallback_visual_type=VisualType.PROCESS_FLOW,
        min_items=3,
        max_items=5,
        description="Cyclical feedback loop or recurring stage flow",
    ),
    VisualType.QUOTE: ArchetypeDescriptor(
        visual_type=VisualType.QUOTE,
        preferred_archetype="quote",
        fallback_archetype="hero",
        fallback_visual_type=VisualType.HERO,
        min_items=1,
        max_items=2,
        description="Impact quotation statement with attribution badge",
    ),
    VisualType.CARD_GRID: ArchetypeDescriptor(
        visual_type=VisualType.CARD_GRID,
        preferred_archetype="three_card_row",
        fallback_archetype="title_body",
        fallback_visual_type=VisualType.TEXT,
        min_items=2,
        max_items=6,
        description="Uniform card grid (two-column, three-card row, or four-card 2x2)",
    ),
    VisualType.TEXT: ArchetypeDescriptor(
        visual_type=VisualType.TEXT,
        preferred_archetype="title_body",
        fallback_archetype="blank",
        fallback_visual_type=VisualType.NONE,
        min_items=1,
        max_items=6,
        description="Structured narrative lead + bullet points",
    ),
    VisualType.NONE: ArchetypeDescriptor(
        visual_type=VisualType.NONE,
        preferred_archetype="blank",
        fallback_archetype="blank",
        fallback_visual_type=VisualType.NONE,
        min_items=0,
        max_items=12,
        description="Freeform canvas",
    ),
}


def get_archetype_descriptor(visual_type: VisualType) -> ArchetypeDescriptor:
    """Retrieve the descriptor mapping for a VisualType with safe fallback."""
    return ARCHETYPE_MAPPINGS.get(
        visual_type,
        ARCHETYPE_MAPPINGS[VisualType.CARD_GRID],
    )


def resolve_card_grid_archetype(element_count: int) -> str:
    """Resolve specific card grid archetype based on item count."""
    if element_count == 2:
        return "two_column"
    elif element_count == 4:
        return "four_card_grid"
    return "three_card_row"
