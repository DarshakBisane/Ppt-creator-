"""Domain models for presentation intelligence, storytelling, content planning, and QA."""

from typing import Literal
from pydantic import BaseModel, Field

from backend.app.domain.enums import (
    ContentDepth,
    ContentIssueType,
    ContentSeverity,
    NarrativeRole,
    NarrativeStrategy,
    VisualType,
)


class TopicAnalysis(BaseModel):
    """Semantic analysis of the user topic and domain framing."""

    topic: str
    domain: str = Field(default="general", description="Primary domain e.g. technology, healthcare, finance")
    target_audience: str = Field(default="executives", description="Identified or provided audience")
    presentation_purpose: str = Field(default="strategic_briefing", description="Core objective")
    complexity_level: Literal["foundational", "intermediate", "advanced"] = "intermediate"
    key_themes: list[str] = Field(default_factory=list, description="Extracted critical themes")
    domain_terminology: list[str] = Field(default_factory=list, description="Key domain concepts to explain")
    recommended_strategy: NarrativeStrategy = Field(default=NarrativeStrategy.BUSINESS_EXECUTIVE)
    recommended_depth: ContentDepth = Field(default=ContentDepth.PROFESSIONAL)
    suggested_slide_count: int = Field(default=8, ge=3, le=30)


class SlideStoryboardItem(BaseModel):
    """Storyboard node defining a single slide's narrative intent and visual structure."""

    slide_number: int = Field(..., ge=1)
    narrative_role: NarrativeRole
    objective: str = Field(..., description="Why this slide exists in the story")
    suggested_title: str = Field(..., description="Action/insight-driven title proposal")
    suggested_subtitle: str | None = None
    key_message: str = Field(..., description="Core takeaway message to communicate")
    visual_intent: str = Field(..., description="Rationale for selected visual form")
    suggested_visual_type: VisualType = Field(default=VisualType.CARD_GRID)
    data_requirements: str | None = None
    transition_to_next: str | None = None


class PresentationStoryboard(BaseModel):
    """Deck-level blueprint outlining narrative progression and visual rhythm."""

    presentation_title: str
    topic: str
    narrative_strategy: NarrativeStrategy
    content_depth: ContentDepth
    arc_summary: str = Field(..., description="High-level presentation storytelling arc description")
    slides: list[SlideStoryboardItem] = Field(..., min_length=1)


class ContentQAIssue(BaseModel):
    """Single defect detected by deterministic Content QA."""

    slide_number: int = Field(..., ge=1)
    issue_type: ContentIssueType
    severity: ContentSeverity
    description: str
    recommendation: str


class SlideContentQAResult(BaseModel):
    """Content QA evaluation for a single slide."""

    slide_number: int
    score: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    title: str
    title_word_count: int
    bullet_count: int
    has_takeaway: bool
    is_card_grid: bool
    issues: list[ContentQAIssue] = Field(default_factory=list)


class ContentQAResult(BaseModel):
    """Complete presentation Content QA report with deterministic scoring."""

    passed: bool
    quality_score: float = Field(..., ge=0.0, le=100.0)
    total_issues: int = 0
    critical_issues: int = 0
    errors: int = 0
    warnings: int = 0
    card_grid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    narrative_coherence_score: float = Field(default=100.0, ge=0.0, le=100.0)
    slide_results: list[SlideContentQAResult] = Field(default_factory=list)
    issues: list[ContentQAIssue] = Field(default_factory=list)


class PresentationQualityScore(BaseModel):
    """Executive composite presentation quality score across 6 weighted dimensions."""

    composite_score: float = Field(..., ge=0.0, le=100.0)
    content_score: float = Field(..., ge=0.0, le=100.0)
    narrative_score: float = Field(..., ge=0.0, le=100.0)
    visual_score: float = Field(..., ge=0.0, le=100.0)
    layout_score: float = Field(..., ge=0.0, le=100.0)
    density_score: float = Field(..., ge=0.0, le=100.0)
    consistency_score: float = Field(..., ge=0.0, le=100.0)
    status: Literal["EXCELLENT", "GOOD", "NEEDS_REFINEMENT", "FAILED"] = "GOOD"
    metrics_summary: dict[str, float] = Field(default_factory=dict)
