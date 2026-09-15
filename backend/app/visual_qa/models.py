"""Strongly typed domain models and results for Visual Quality Assurance and Auto-Correction."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from backend.app.domain.enums import VisualType
from backend.app.layout.models import PresentationLayoutResult, SlideLayoutResult


class QASeverity(str, Enum):
    """Severity classification of visual layout issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QAIssueType(str, Enum):
    """Categorized visual and geometric issue types."""

    TEXT_OVERFLOW = "text_overflow"
    ELEMENT_OVERFLOW = "element_overflow"
    OUT_OF_BOUNDS = "out_of_bounds"
    SIBLING_COLLISION = "sibling_collision"
    CONTAINMENT_VIOLATION = "containment_violation"
    CONNECTOR_INVALID = "connector_invalid"
    CONNECTOR_CONTENT_OVERLAP = "connector_content_overlap"
    DENSITY_HIGH = "density_high"
    UNSAFE_MARGIN = "unsafe_margin"
    INVALID_GEOMETRY = "invalid_geometry"
    EMPTY_VISUAL = "empty_visual"
    STRUCTURAL_ERROR = "structural_error"
    ARCHETYPE_VIOLATION = "archetype_violation"


class LayerCategory(str, Enum):
    """Semantic z-index layer classification for collision rules."""

    BACKGROUND = "background"
    CONTAINER = "container"
    CONTENT = "content"
    CONNECTOR = "connector"
    DECORATION = "decoration"


class DensityLevel(str, Enum):
    """Slide visual information density rating."""

    LOW = "low"
    BALANCED = "balanced"
    HIGH = "high"
    CRITICAL = "critical"


class QAIssue(BaseModel):
    """Structured description of a detected visual layout defect."""

    issue_type: QAIssueType = Field(..., description="Categorized issue type")
    severity: QASeverity = Field(..., description="Issue severity level")
    slide_id: str = Field(..., description="Target slide identifier")
    slide_index: int = Field(default=1, description="1-indexed slide sequence number")
    element_id: str | None = Field(default=None, description="Primary defective element ID")
    related_element_ids: list[str] = Field(
        default_factory=list, description="Associated or colliding element IDs"
    )
    message: str = Field(..., description="Human-readable explanation of the defect")
    measured_value: float | int | str | None = Field(
        default=None, description="Measured geometric or numerical value"
    )
    expected_value: float | int | str | None = Field(
        default=None, description="Allowed or expected constraint threshold"
    )
    correction_strategy: str | None = Field(
        default=None, description="Deterministic strategy proposed or applied"
    )
    is_correctable: bool = Field(
        default=True, description="Whether this issue can be repaired deterministically"
    )


class CorrectionRecord(BaseModel):
    """Audit log entry of a deterministic correction action."""

    pass_number: int = Field(..., ge=1, le=3, description="Correction pass number (1, 2, or 3)")
    issue_type: QAIssueType = Field(..., description="Target issue type repaired")
    strategy: str = Field(..., description="Specific repair strategy applied")
    element_id: str | None = Field(default=None, description="Repaired element ID")
    description: str = Field(..., description="Explanation of geometric adjustments")
    success: bool = Field(default=True, description="Whether the correction action succeeded")
    score_delta: float = Field(default=0.0, description="Quality score change after correction")


class SlideDensityMetrics(BaseModel):
    """Deterministic visual density measurements for a slide."""

    occupied_area_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of slide area covered by elements"
    )
    whitespace_ratio: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Fraction of slide remaining as whitespace"
    )
    element_count: int = Field(default=0, ge=0, description="Total number of visible elements")
    content_count: int = Field(default=0, ge=0, description="Number of primary content elements")
    character_count: int = Field(default=0, ge=0, description="Total characters in slide content")
    density_level: DensityLevel = Field(
        default=DensityLevel.BALANCED, description="Archetype-aware density level"
    )
    is_balanced: bool = Field(default=True, description="Whether slide is comfortably balanced")


class PassRecord(BaseModel):
    """Audit tracking record of an executed auto-correction pass."""

    pass_number: int = Field(..., ge=1, le=3)
    strategy_name: str
    score_before: float
    score_after: float
    issues_count_before: int
    issues_count_after: int
    accepted: bool
    rationale: str = ""


class SlideQAResult(BaseModel):
    """Evaluation result and diagnostics for a single slide layout."""

    slide_id: str
    slide_number: int
    passed: bool
    visual_type: VisualType
    archetype: str
    quality_score: float = Field(..., ge=0.0, le=100.0)
    issues: list[QAIssue] = Field(default_factory=list)
    density: SlideDensityMetrics = Field(default_factory=SlideDensityMetrics)
    corrections_applied: list[CorrectionRecord] = Field(default_factory=list)
    passes_executed: int = Field(default=1, ge=1, le=3)
    layout: SlideLayoutResult

    @property
    def critical_issues(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == QASeverity.CRITICAL]

    @property
    def error_issues(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == QASeverity.ERROR]

    @property
    def warning_issues(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == QASeverity.WARNING]


class VisualQAResult(BaseModel):
    """Comprehensive evaluation result for an entire presentation layout."""

    passed: bool
    final_status: str = Field(..., description="Status summary (e.g. PASSED, CORRECTED, WARNINGS, FAILED)")
    total_issues: int = 0
    critical_issues: int = 0
    errors: int = 0
    warnings: int = 0
    passes_executed: int = Field(default=1, ge=1, le=3)
    corrections_applied: list[CorrectionRecord] = Field(default_factory=list)
    final_quality_score: float = Field(..., ge=0.0, le=100.0)
    slide_results: list[SlideQAResult] = Field(default_factory=list)
    unresolved_issues: list[QAIssue] = Field(default_factory=list)
    correction_history: list[PassRecord] = Field(default_factory=list)
    layout: PresentationLayoutResult | None = None
