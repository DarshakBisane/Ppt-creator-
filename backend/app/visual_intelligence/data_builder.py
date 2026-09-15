"""Conservative data builder synthesizing domain visual models (Timeline, ProcessFlow, Chart, Table)."""

import re
from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.constants import (
    MAX_CHART_POINTS,
    MAX_PROCESS_STEPS,
    MAX_TIMELINE_MILESTONES,
)
from backend.app.domain.enums import (
    DataSource,
    ProcessDirection,
    TimelineStatus,
    VisualType,
)
from backend.app.domain.presentation import Slide
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
)


class VisualDataBuilder:
    """Builds or extracts structured domain visual models from slide text and elements."""

    @staticmethod
    def build_timeline_data(slide: Slide) -> TimelineData | None:
        """Extract milestones and dates from slide elements to build TimelineData."""
        if slide.visual_plan and slide.visual_plan.timeline_data:
            return slide.visual_plan.timeline_data

        milestones: list[TimelineMilestone] = []

        # Extract from elements
        date_pattern = re.compile(r"\b(19\d\d|20\d\d|Q[1-4]|Phase\s*\d+|Stage\s*\d+|Month\s*\d+|Year\s*\d+)\b", re.IGNORECASE)

        for i, elem in enumerate(slide.elements):
            text = elem.text_content.text if elem.text_content else (elem.card_content.title if elem.card_content else "")
            desc = elem.card_content.body if elem.card_content else ""

            if not text:
                continue

            # Check if text has a date marker
            m = date_pattern.search(text)
            date_str = m.group(1) if m else f"M{i+1}"
            label = text.replace(date_str, "").strip(" -:–—") or f"Milestone {i+1}"

            milestones.append(
                TimelineMilestone(
                    label=label[:100],
                    date=date_str[:50],
                    description=desc[:300],
                    status=TimelineStatus.COMPLETED if i == 0 else TimelineStatus.PLANNED,
                )
            )

        if len(milestones) >= 2:
            return TimelineData(
                title=slide.title,
                milestones=milestones[:MAX_TIMELINE_MILESTONES],
            )

        return None

    @staticmethod
    def build_process_flow_data(slide: Slide) -> ProcessFlowData | None:
        """Extract ordered steps from slide elements to build ProcessFlowData."""
        if slide.visual_plan and slide.visual_plan.process_flow_data:
            return slide.visual_plan.process_flow_data

        steps: list[ProcessStep] = []

        for i, elem in enumerate(slide.elements):
            title = elem.card_content.title if elem.card_content else (elem.text_content.text if elem.text_content else "")
            desc = elem.card_content.body if elem.card_content else ""

            if not title:
                continue

            clean_title = re.sub(r"^(Step|Phase|Stage|\d+)[.:\- ]*", "", title, flags=re.IGNORECASE).strip() or f"Step {i+1}"

            steps.append(
                ProcessStep(
                    id=f"step_{i+1}",
                    title=clean_title[:100],
                    description=desc[:300],
                    order=i + 1,
                )
            )

        if len(steps) >= 2:
            return ProcessFlowData(
                direction=ProcessDirection.HORIZONTAL,
                steps=steps[:MAX_PROCESS_STEPS],
            )

        return None

    @staticmethod
    def build_table_data(slide: Slide) -> TableData | None:
        """Extract tabular rows and columns to build TableData."""
        if slide.visual_plan and slide.visual_plan.table_data:
            return slide.visual_plan.table_data

        # If slide has card elements, build structured comparison table
        if len(slide.elements) >= 2:
            cols = [TableColumn(key="feature", label="Feature / Dimension")]
            for i, elem in enumerate(slide.elements[:4]):
                name = elem.card_content.title if elem.card_content else f"Option {chr(65 + i)}"
                cols.append(TableColumn(key=f"col_{i+1}", label=name[:50]))

            row1_cells = ["Overview"] + [elem.card_content.body[:100] if elem.card_content else "Standard" for elem in slide.elements[:4]]
            row2_cells = ["Status"] + ["Supported" for _ in slide.elements[:4]]

            rows = [
                TableRow(cells=row1_cells),
                TableRow(cells=row2_cells),
            ]

            return TableData(
                columns=cols,
                rows=rows,
                has_header=True,
            )

        return None

    @staticmethod
    def build_chart_data(slide: Slide, chart_type: str = "column") -> ChartData | None:
        """Build ChartData only if valid series and categories exist."""
        if slide.visual_plan and slide.visual_plan.chart_data:
            return slide.visual_plan.chart_data

        # Harvest KPI or numeric elements
        categories: list[str] = []
        values: list[float] = []

        num_regex = re.compile(r"(\d+(\.\d+)?)")

        for elem in slide.elements:
            if elem.kpi_content:
                m = num_regex.search(elem.kpi_content.value)
                if m:
                    categories.append(elem.kpi_content.label or "Metric")
                    values.append(float(m.group(1)))
            elif elem.card_content:
                m = num_regex.search(elem.card_content.title) or num_regex.search(elem.card_content.body)
                if m:
                    categories.append(elem.card_content.title[:20])
                    values.append(float(m.group(1)))

        if len(categories) >= 2 and len(values) == len(categories):
            return ChartData(
                chart_type=chart_type,
                title=slide.title,
                categories=categories[:MAX_CHART_POINTS],
                series=[ChartSeries(name="Value", values=values[:MAX_CHART_POINTS])],
                data_source=DataSource.ILLUSTRATIVE,
                is_illustrative=True,
            )

        return None
