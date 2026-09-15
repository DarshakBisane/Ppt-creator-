"""Native PowerPoint chart rendering."""

from typing import Any
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.design_system import DesignSystem
from backend.app.layout.models import ElementGeometry


def render_chart_element(
    slide_shape_tree: Any,
    elem: ElementGeometry,
    ds: DesignSystem,
) -> Any:
    """Render a native PowerPoint chart populated from ChartData."""
    x_emu, y_emu, w_emu, h_emu = elem.rect.to_emu()
    chart_domain: ChartData | None = elem.content_data if isinstance(elem.content_data, ChartData) else None

    chart_type_map = {
        "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "stacked_column": XL_CHART_TYPE.COLUMN_STACKED,
        "bar": XL_CHART_TYPE.BAR_CLUSTERED,
        "stacked_bar": XL_CHART_TYPE.BAR_STACKED,
        "line": XL_CHART_TYPE.LINE,
        "pie": XL_CHART_TYPE.PIE,
        "donut": XL_CHART_TYPE.DOUGHNUT,
        "area": XL_CHART_TYPE.AREA,
    }

    if not chart_domain:
        # Default chart fallback
        c_type = XL_CHART_TYPE.COLUMN_CLUSTERED
        c_data = CategoryChartData()
        c_data.categories = ["Q1", "Q2", "Q3", "Q4"]
        c_data.add_series("Efficiency Gain", (25.0, 40.0, 65.0, 90.0))
        c_data.add_series("Cost Reduction", (15.0, 28.0, 45.0, 60.0))
        title = "Quarterly Impact"
    else:
        c_type = chart_type_map.get(chart_domain.chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)
        c_data = CategoryChartData()
        c_data.categories = chart_domain.categories
        for s in chart_domain.series:
            c_data.add_series(s.name, tuple(s.values))
        title = chart_domain.title

    chart_shape = slide_shape_tree.add_chart(
        c_type,
        x_emu,
        y_emu,
        w_emu,
        h_emu,
        c_data,
    )

    chart = chart_shape.chart
    chart.has_legend = True
    chart.has_title = True
    chart.chart_title.text_frame.text = title

    return chart_shape
