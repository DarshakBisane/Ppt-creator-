"""Registry mapping semantic visual archetypes to deterministic layout resolvers."""

from backend.app.domain.enums import VisualType
from backend.app.layout.archetypes import (
    AnatomyResolver,
    ArchitectureResolver,
    BaseArchetypeResolver,
    BlankResolver,
    ChartInsightResolver,
    ComparisonResolver,
    DecisionFlowResolver,
    FlowchartResolver,
    FourCardGridResolver,
    HeroResolver,
    HierarchyTreeResolver,
    KPIDashboardResolver,
    LayeredStackResolver,
    LifecycleResolver,
    MatrixResolver,
    ProcessFlowResolver,
    QuoteResolver,
    RoadmapResolver,
    TableSummaryResolver,
    ThreeCardRowResolver,
    TimelineResolver,
    TitleBodyResolver,
    TwoColumnResolver,
)


class LayoutRegistry:
    """Central registry for visual layout archetype resolvers."""

    def __init__(self) -> None:
        self._resolvers: dict[str, BaseArchetypeResolver] = {}
        self._default_resolver = BlankResolver()
        self._register_builtins()

    def _register_builtins(self) -> None:
        # Standard VisualType mappings
        self.register(VisualType.NONE.value, BlankResolver())
        self.register(VisualType.IMAGE.value, BlankResolver())
        self.register(VisualType.ICON_GROUP.value, BlankResolver())
        self.register(VisualType.TEXT.value, TitleBodyResolver())
        self.register(VisualType.HERO.value, HeroResolver())
        self.register(VisualType.CARD_GRID.value, ThreeCardRowResolver())
        self.register("three_card_row", ThreeCardRowResolver())
        self.register("four_card_grid", FourCardGridResolver())
        self.register("two_column", TwoColumnResolver())
        self.register(VisualType.KPI.value, KPIDashboardResolver())
        self.register(VisualType.COMPARISON.value, ComparisonResolver())
        self.register(VisualType.TIMELINE.value, TimelineResolver())
        self.register(VisualType.PROCESS_FLOW.value, ProcessFlowResolver())
        self.register(VisualType.FLOWCHART.value, FlowchartResolver())
        self.register(VisualType.DIAGRAM.value, FlowchartResolver())
        self.register(VisualType.HIERARCHY.value, HierarchyTreeResolver())
        self.register(VisualType.TREE.value, HierarchyTreeResolver())
        self.register(VisualType.ARCHITECTURE.value, ArchitectureResolver())
        self.register(VisualType.MATRIX.value, MatrixResolver())
        self.register(VisualType.TABLE.value, TableSummaryResolver())
        self.register(VisualType.BAR_CHART.value, ChartInsightResolver())
        self.register(VisualType.COLUMN_CHART.value, ChartInsightResolver())
        self.register(VisualType.LINE_CHART.value, ChartInsightResolver())
        self.register(VisualType.PIE_CHART.value, ChartInsightResolver())
        self.register(VisualType.DONUT_CHART.value, ChartInsightResolver())
        self.register(VisualType.QUOTE.value, QuoteResolver())
        self.register(VisualType.ROADMAP.value, RoadmapResolver())
        self.register(VisualType.CYCLE.value, LifecycleResolver())
        # Specialized diagram compositions
        self.register(VisualType.ANATOMY.value, AnatomyResolver())
        self.register(VisualType.LIFECYCLE.value, LifecycleResolver())
        self.register(VisualType.DECISION_FLOW.value, DecisionFlowResolver())
        self.register(VisualType.LAYERED_STACK.value, LayeredStackResolver())

    def register(self, key: str, resolver: BaseArchetypeResolver) -> None:
        """Register a resolver for a visual archetype key."""
        self._resolvers[key.lower().strip()] = resolver

    def get_resolver(self, visual_type: VisualType | str, element_count: int = 0) -> BaseArchetypeResolver:
        """Lookup resolver with smart fallback for card grids and unknown types."""
        type_str = visual_type.value if isinstance(visual_type, VisualType) else str(visual_type)
        key = type_str.lower().strip()

        # Dynamic selection for card grids based on element count
        if key == VisualType.CARD_GRID.value:
            if element_count == 4:
                return self._resolvers.get("four_card_grid", ThreeCardRowResolver())
            elif element_count == 2:
                return self._resolvers.get("two_column", ThreeCardRowResolver())
            return self._resolvers.get("three_card_row", ThreeCardRowResolver())

        return self._resolvers.get(key, self._default_resolver)


# Global default registry instance
default_layout_registry = LayoutRegistry()
