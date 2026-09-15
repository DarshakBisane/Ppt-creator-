"""Semantic visual structures and visual plan models."""

from typing import Literal
from pydantic import BaseModel, Field

from backend.app.domain.charts import ChartData
from backend.app.domain.constants import (
    MAX_PROCESS_STEPS,
    MAX_TIMELINE_MILESTONES,
)
from backend.app.domain.enums import (
    ProcessDirection,
    TimelineStatus,
    VisualType,
)
from backend.app.domain.tables import TableData


class TimelineMilestone(BaseModel):
    """Milestone node on a timeline."""

    label: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=300)
    status: TimelineStatus = Field(default=TimelineStatus.PLANNED)


class TimelineData(BaseModel):
    """Semantic timeline rail specification."""

    title: str | None = Field(default=None, max_length=150)
    milestones: list[TimelineMilestone] = Field(
        ..., min_length=2, max_length=MAX_TIMELINE_MILESTONES
    )


class ProcessStep(BaseModel):
    """Single step in a process flowchart or workflow."""

    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=300)
    order: int = Field(..., ge=1)


class ProcessFlowData(BaseModel):
    """Sequential or cyclical process flow model."""

    direction: ProcessDirection = Field(default=ProcessDirection.HORIZONTAL)
    steps: list[ProcessStep] = Field(..., min_length=2, max_length=MAX_PROCESS_STEPS)


class VisualPlan(BaseModel):
    """Semantic visual plan instructing deterministic layout and rendering engines."""

    visual_type: VisualType = Field(default=VisualType.NONE)
    intent: str = Field(default="", max_length=300, description="Semantic rationale for this visual structure")
    priority: Literal["low", "medium", "high", "hero"] = Field(default="medium")
    chart_data: ChartData | None = None
    table_data: TableData | None = None
    timeline_data: TimelineData | None = None
    process_flow_data: ProcessFlowData | None = None
