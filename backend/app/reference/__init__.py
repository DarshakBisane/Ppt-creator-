"""Reference PPT Intelligence Analyzer Package."""

from backend.app.reference.analyzer import (
    ReferencePPTAnalyzer,
    analyze_reference_presentation,
    default_reference_analyzer,
)
from backend.app.reference.exceptions import (
    InvalidReferencePPTXError,
    ReferenceAnalysisError,
    ReferencePackageTooLargeError,
    ReferencePPTError,
    ReferenceXMLSecurityError,
)
from backend.app.reference.inspector import SafePPTXPackage
from backend.app.reference.models import (
    ExtractedColor,
    ExtractedFont,
    ExtractedMotif,
    ReferenceAnalysisSummary,
)

__all__ = [
    # Facade & Helpers
    "ReferencePPTAnalyzer",
    "default_reference_analyzer",
    "analyze_reference_presentation",
    "SafePPTXPackage",
    # Models
    "ExtractedColor",
    "ExtractedFont",
    "ExtractedMotif",
    "ReferenceAnalysisSummary",
    # Exceptions
    "ReferencePPTError",
    "InvalidReferencePPTXError",
    "ReferencePackageTooLargeError",
    "ReferenceXMLSecurityError",
    "ReferenceAnalysisError",
]
