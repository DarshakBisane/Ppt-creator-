"""Controlled domain enumerations."""

from enum import Enum


class NarrativeRole(str, Enum):
    """Semantic narrative role of a slide within the presentation flow."""

    TITLE = "title"
    CONTEXT = "context"
    PROBLEM = "problem"
    INSIGHT = "insight"
    PROCESS = "process"
    COMPARISON = "comparison"
    EVIDENCE = "evidence"
    SOLUTION = "solution"
    ARCHITECTURE = "architecture"
    TIMELINE = "timeline"
    CASE_STUDY = "case_study"
    SUMMARY = "summary"
    CONCLUSION = "conclusion"
    CALL_TO_ACTION = "call_to_action"


class VisualType(str, Enum):
    """Semantic visual representations for slide content."""

    NONE = "none"
    HERO = "hero"
    TEXT = "text"
    KPI = "kpi"
    CARD_GRID = "card_grid"
    COMPARISON = "comparison"
    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    COLUMN_CHART = "column_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    TIMELINE = "timeline"
    PROCESS_FLOW = "process_flow"
    FLOWCHART = "flowchart"
    HIERARCHY = "hierarchy"
    TREE = "tree"
    CYCLE = "cycle"
    ARCHITECTURE = "architecture"
    ROADMAP = "roadmap"
    MATRIX = "matrix"
    DIAGRAM = "diagram"
    QUOTE = "quote"
    IMAGE = "image"
    ICON_GROUP = "icon_group"
    ANATOMY = "anatomy"
    DECISION_FLOW = "decision_flow"
    LIFECYCLE = "lifecycle"
    LAYERED_STACK = "layered_stack"


class ElementType(str, Enum):
    """Semantic element category."""

    TEXT = "text"
    HEADING = "heading"
    BODY = "body"
    LABEL = "label"
    KPI = "kpi"
    CARD = "card"
    IMAGE = "image"
    ICON = "icon"
    SHAPE = "shape"
    CONNECTOR = "connector"
    TABLE = "table"
    CHART = "chart"
    TIMELINE = "timeline"
    PROCESS_FLOW = "process_flow"
    GROUP = "group"


class DataSource(str, Enum):
    """Provenance of data values to prevent fabricated statistics."""

    USER_PROVIDED = "user_provided"
    REFERENCE_DOCUMENT = "reference_document"
    AI_DERIVED = "ai_derived"
    ILLUSTRATIVE = "illustrative"
    UNKNOWN = "unknown"


class TimelineStatus(str, Enum):
    """Milestone status on a timeline."""

    PLANNED = "planned"
    CURRENT = "current"
    COMPLETED = "completed"
    MILESTONE = "milestone"


class ProcessDirection(str, Enum):
    """Direction of process flow."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    AUTO = "auto"


class TokenSource(str, Enum):
    """Origin of design tokens."""

    DEFAULT = "default"
    EXTRACTED = "extracted"
    INFERRED = "inferred"
    USER_DEFINED = "user_defined"
    FALLBACK = "fallback"


class Density(str, Enum):
    """Visual density preference."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Alignment(str, Enum):
    """Horizontal alignment."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class WhitespacePreference(str, Enum):
    """Whitespace distribution preference."""

    SPACIOUS = "spacious"
    BALANCED = "balanced"
    COMPACT = "compact"


class JobStatus(str, Enum):
    """Generation job execution status."""

    IDLE = "idle"
    VALIDATING = "validating"
    QUEUED = "queued"
    PLANNING = "planning"
    DESIGNING = "designing"
    RENDERING = "rendering"
    QA = "qa"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NarrativeStrategy(str, Enum):
    """Strategic storytelling arc for deck generation."""

    BUSINESS_EXECUTIVE = "business_executive"
    TECHNICAL_ARCHITECTURE = "technical_architecture"
    ACADEMIC_EDUCATIONAL = "academic_educational"
    RESEARCH_ANALYTICAL = "research_analytical"
    PRODUCT_PITCH = "product_pitch"


class ContentDepth(str, Enum):
    """Depth level for content generation."""

    CONCISE = "concise"
    STANDARD = "standard"
    DETAILED = "detailed"
    PROFESSIONAL = "professional"


class ContentIssueType(str, Enum):
    """Category of deterministic content QA issues."""

    GENERIC_TITLE = "generic_title"
    SHALLOW_CONTENT = "shallow_content"
    EXCESSIVE_CARDS = "excessive_cards"
    MISSING_TAKEAWAY = "missing_takeaway"
    DUPLICATE_CONTENT = "duplicate_content"
    UNSUPPORTED_STAT = "unsupported_stat"
    WEAK_VISUAL_ALIGNMENT = "weak_visual_alignment"
    STRUCTURAL_REPETITION = "structural_repetition"


class ContentSeverity(str, Enum):
    """Severity of content QA issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

