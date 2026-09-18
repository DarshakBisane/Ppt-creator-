"""Canonical Presentation Domain Package."""

from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.charts import ChartData, ChartSeries
from backend.app.domain.constants import CURRENT_SCHEMA_VERSION
from backend.app.domain.content import (
    BadgeContent,
    CardContent,
    IconContent,
    KPIContent,
    TextContent,
)
from backend.app.domain.design_system import (
    ColorToken,
    DesignSystem,
    LayoutPreferences,
    Palette,
    ShapeStyle,
    SpacingScale,
    TypographyStyle,
    TypographySystem,
)
from backend.app.domain.elements import Element
from backend.app.domain.enums import (
    Alignment,
    ContentDepth,
    ContentIssueType,
    ContentSeverity,
    DataSource,
    Density,
    ElementType,
    JobStatus,
    NarrativeRole,
    NarrativeStrategy,
    ProcessDirection,
    TimelineStatus,
    TokenSource,
    VisualType,
    WhitespacePreference,
)
from backend.app.domain.jobs import JobError, JobProgress, JobState
from backend.app.domain.presentation import (
    GenerationMetadata,
    Presentation,
    PresentationMetadata,
    Slide,
)
from backend.app.domain.tables import TableColumn, TableData, TableRow
from backend.app.domain.visuals import (
    ProcessFlowData,
    ProcessStep,
    TimelineData,
    TimelineMilestone,
    VisualPlan,
)

__all__ = [
    # Constants
    "CURRENT_SCHEMA_VERSION",
    # Enums
    "Alignment",
    "ContentDepth",
    "ContentIssueType",
    "ContentSeverity",
    "DataSource",
    "Density",
    "ElementType",
    "JobStatus",
    "NarrativeRole",
    "NarrativeStrategy",
    "ProcessDirection",
    "TimelineStatus",
    "TokenSource",
    "VisualType",
    "WhitespacePreference",
    # Canvas & Design System
    "CanvasSpec",
    "ColorToken",
    "DesignSystem",
    "LayoutPreferences",
    "Palette",
    "ShapeStyle",
    "SpacingScale",
    "TypographyStyle",
    "TypographySystem",
    # Semantic Content
    "BadgeContent",
    "CardContent",
    "IconContent",
    "KPIContent",
    "TextContent",
    # Elements & Visuals
    "ChartData",
    "ChartSeries",
    "Element",
    "ProcessFlowData",
    "ProcessStep",
    "TableColumn",
    "TableData",
    "TableRow",
    "TimelineData",
    "TimelineMilestone",
    "VisualPlan",
    # Presentation
    "Presentation",
    "PresentationMetadata",
    "Slide",
    # Jobs
    "JobError",
    "JobProgress",
    "JobState",
]
