"""Tests for visual layout archetypes (KPI, Comparison, Timeline, Process, Flowchart, Tree, Arch, Matrix, Table, Chart, Quote, Roadmap)."""

import pytest

from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.content import KPIContent
from backend.app.domain.design_system import DesignSystem
from backend.app.domain.elements import Element
from backend.app.domain.enums import ElementType, NarrativeRole, TimelineStatus, VisualType
from backend.app.domain.presentation import Slide
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
)
from backend.app.layout.engine import LayoutEngine


@pytest.fixture
def engine() -> LayoutEngine:
    return LayoutEngine()


@pytest.fixture
def ds() -> DesignSystem:
    return DesignSystem()


def test_kpi_dashboard_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_kpi",
        slide_number=2,
        title="Impact Metrics",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(visual_type=VisualType.KPI),
        elements=[
            Element(id="k1", type=ElementType.KPI, kpi_content=KPIContent(label="Latency", value="<10ms", trend="up")),
            Element(id="k2", type=ElementType.KPI, kpi_content=KPIContent(label="Throughput", value="100k", trend="up")),
            Element(id="k3", type=ElementType.KPI, kpi_content=KPIContent(label="Availability", value="99.99%")),
        ],
    )
    res = engine.layout_slide(slide, ds)
    kpis = [e for e in res.elements if e.semantic_type == ElementType.KPI]
    assert len(kpis) == 3
    # Check width uniformity within 1px remainder tolerance
    assert abs(kpis[0].rect.width - kpis[1].rect.width) <= 1
    assert abs(kpis[1].rect.width - kpis[2].rect.width) <= 1



def test_comparison_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_cmp",
        slide_number=3,
        title="Architecture Comparison",
        narrative_role=NarrativeRole.COMPARISON,
        visual_plan=VisualPlan(visual_type=VisualType.COMPARISON),
    )
    res = engine.layout_slide(slide, ds)
    left_panel = next(e for e in res.elements if e.role == "comparison_left")
    right_panel = next(e for e in res.elements if e.role == "comparison_right")
    vs_badge = next(e for e in res.elements if e.role == "vs_badge")

    assert left_panel.rect.right < vs_badge.rect.x
    assert vs_badge.rect.right < right_panel.rect.x


def test_timeline_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_time",
        slide_number=4,
        title="Program Horizon",
        narrative_role=NarrativeRole.TIMELINE,
        visual_plan=VisualPlan(
            visual_type=VisualType.TIMELINE,
            timeline_data=TimelineData(
                milestones=[
                    TimelineMilestone(label="Alpha", date="Jan", status=TimelineStatus.COMPLETED),
                    TimelineMilestone(label="Beta", date="Mar", status=TimelineStatus.CURRENT),
                    TimelineMilestone(label="GA", date="Jun", status=TimelineStatus.PLANNED),
                ]
            ),
        ),
    )
    res = engine.layout_slide(slide, ds)
    assert any(e.role == "spine" for e in res.elements)
    cards = [e for e in res.elements if e.role == "milestone_card"]
    assert len(cards) == 3
    assert len(res.connectors) == 3


def test_process_flow_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_pf",
        slide_number=5,
        title="Execution Lifecycle",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(
            visual_type=VisualType.PROCESS_FLOW,
            process_flow_data=ProcessFlowData(
                steps=[
                    ProcessStep(id="st1", title="Input", order=1),
                    ProcessStep(id="st2", title="Transform", order=2),
                    ProcessStep(id="st3", title="Output", order=3),
                ]
            ),
        ),
    )
    res = engine.layout_slide(slide, ds)
    steps = [e for e in res.elements if e.role == "process_step"]
    assert len(steps) == 3
    assert len(res.connectors) == 2  # Connectors between st1->st2 and st2->st3


def test_flowchart_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_flow",
        slide_number=6,
        title="Decision Tree",
        narrative_role=NarrativeRole.PROCESS,
        visual_plan=VisualPlan(visual_type=VisualType.FLOWCHART),
    )
    res = engine.layout_slide(slide, ds)
    nodes = [e for e in res.elements if e.role == "flowchart_node"]
    assert len(nodes) == 3
    assert len(res.connectors) == 2


def test_hierarchy_tree_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_tree",
        slide_number=7,
        title="System Hierarchy",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.HIERARCHY),
    )
    res = engine.layout_slide(slide, ds)
    root = next(e for e in res.elements if e.role == "tree_root")
    children = [e for e in res.elements if e.role == "tree_child"]
    assert len(children) == 3
    assert all(c.rect.y > root.rect.bottom for c in children)
    assert len(res.connectors) == 3


def test_architecture_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_arch",
        slide_number=8,
        title="Layered Architecture",
        narrative_role=NarrativeRole.ARCHITECTURE,
        visual_plan=VisualPlan(visual_type=VisualType.ARCHITECTURE),
    )
    res = engine.layout_slide(slide, ds)
    layers = [e for e in res.elements if e.role == "architecture_layer"]
    assert len(layers) == 4
    for i in range(len(layers) - 1):
        assert layers[i].rect.bottom < layers[i + 1].rect.y
    assert len(res.connectors) == 3


def test_matrix_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_mat",
        slide_number=9,
        title="Priority Matrix",
        narrative_role=NarrativeRole.INSIGHT,
        visual_plan=VisualPlan(visual_type=VisualType.MATRIX),
    )
    res = engine.layout_slide(slide, ds)
    quads = [e for e in res.elements if e.role == "quadrant"]
    assert len(quads) == 4


def test_table_summary_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_tbl",
        slide_number=10,
        title="Benchmark Data",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(
            visual_type=VisualType.TABLE,
            table_data=TableData(
                columns=[TableColumn(key="k1", label="Metric"), TableColumn(key="k2", label="Score")],
                rows=[TableRow(cells=["Latency", "5ms"]), TableRow(cells=["Throughput", "10k"])],
            ),
        ),
    )
    res = engine.layout_slide(slide, ds)
    tbl = next(e for e in res.elements if e.semantic_type == ElementType.TABLE)
    insight = next(e for e in res.elements if e.role == "insight_card")
    assert tbl.rect.right < insight.rect.x


def test_chart_insight_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_chart",
        slide_number=11,
        title="Revenue Trajectory",
        narrative_role=NarrativeRole.EVIDENCE,
        visual_plan=VisualPlan(
            visual_type=VisualType.COLUMN_CHART,
            chart_data=ChartData(
                chart_type="column",
                title="Revenue (USD)",
                categories=["2024", "2025", "2026"],
                series=[ChartSeries(name="Sales", values=[10.0, 20.0, 35.0])],
            ),
        ),
    )
    res = engine.layout_slide(slide, ds)
    chart = next(e for e in res.elements if e.semantic_type == ElementType.CHART)
    insight = next(e for e in res.elements if e.role == "insight_panel")
    assert chart.rect.right < insight.rect.x


def test_quote_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_quote",
        slide_number=12,
        title="Leadership Vision",
        narrative_role=NarrativeRole.CONTEXT,
        visual_plan=VisualPlan(visual_type=VisualType.QUOTE),
    )
    res = engine.layout_slide(slide, ds)
    quote = next(e for e in res.elements if e.role == "quote")
    assert quote.rect.center_x == 960  # Horizontally centered in 1920 canvas


def test_roadmap_layout(engine: LayoutEngine, ds: DesignSystem) -> None:
    slide = Slide(
        id="s_road",
        slide_number=13,
        title="Strategic Roadmap",
        narrative_role=NarrativeRole.TIMELINE,
        visual_plan=VisualPlan(visual_type=VisualType.ROADMAP),
    )
    res = engine.layout_slide(slide, ds)
    lanes = [e for e in res.elements if e.role == "roadmap_horizon"]
    assert len(lanes) == 3
    assert lanes[0].rect.right < lanes[1].rect.x < lanes[2].rect.x
