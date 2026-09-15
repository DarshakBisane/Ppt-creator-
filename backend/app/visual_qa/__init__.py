"""Visual QA & 3-Pass Auto-Correction Subsystem."""

from backend.app.visual_qa.analyzer import (
    SlideVisualAnalyzer,
    analyze_slide_layout,
    calculate_quality_score,
)
from backend.app.visual_qa.correction_pass import (
    ThreePassCorrectionEngine,
    default_correction_engine,
)
from backend.app.visual_qa.exceptions import (
    InvalidGeometryError,
    UnrecoverableLayoutError,
    VisualQAException,
)
from backend.app.visual_qa.models import (
    CorrectionRecord,
    DensityLevel,
    LayerCategory,
    PassRecord,
    QAIssue,
    QAIssueType,
    QASeverity,
    SlideDensityMetrics,
    SlideQAResult,
    VisualQAResult,
)
from backend.app.visual_qa.orchestrator import (
    VisualQAOrchestrator,
    default_qa_orchestrator,
    validate_and_correct_presentation,
    validate_and_correct_slide,
)

__all__ = [
    "QASeverity",
    "QAIssueType",
    "LayerCategory",
    "DensityLevel",
    "QAIssue",
    "CorrectionRecord",
    "SlideDensityMetrics",
    "PassRecord",
    "SlideQAResult",
    "VisualQAResult",
    "VisualQAException",
    "UnrecoverableLayoutError",
    "InvalidGeometryError",
    "SlideVisualAnalyzer",
    "analyze_slide_layout",
    "calculate_quality_score",
    "ThreePassCorrectionEngine",
    "default_correction_engine",
    "VisualQAOrchestrator",
    "default_qa_orchestrator",
    "validate_and_correct_presentation",
    "validate_and_correct_slide",
]
