"""Reference presentation analyzer exceptions."""

from backend.app.core.errors import AppException


class ReferencePPTError(AppException):
    """Base exception for reference PPTX analysis failures."""

    def __init__(self, message: str, code: str = "REFERENCE_PPT_ERROR", details: list | None = None) -> None:
        super().__init__(status_code=400, code=code, message=message, details=details)


class InvalidReferencePPTXError(ReferencePPTError):
    """Raised when the uploaded file is not a valid PowerPoint presentation package."""

    def __init__(self, message: str = "Uploaded file is not a valid PowerPoint (.pptx) presentation.") -> None:
        super().__init__(message=message, code="INVALID_PPTX_PACKAGE")


class ReferencePackageTooLargeError(ReferencePPTError):
    """Raised when the PPTX archive exceeds maximum allowable file count or uncompressed size."""

    def __init__(self, message: str = "Presentation package exceeds size or file count security limits.") -> None:
        super().__init__(message=message, code="PPTX_PACKAGE_TOO_LARGE")


class ReferenceXMLSecurityError(ReferencePPTError):
    """Raised when malicious or forbidden XML constructs (e.g. DTD, external entities) are detected."""

    def __init__(self, message: str = "Forbidden XML entity or DTD declaration detected in presentation.") -> None:
        super().__init__(message=message, code="PPTX_XML_SECURITY_VIOLATION")


class ReferenceAnalysisError(ReferencePPTError):
    """Raised when unrecoverable structural error occurs during reference extraction."""

    def __init__(self, message: str = "Failed to analyze visual design tokens from reference presentation.") -> None:
        super().__init__(message=message, code="REFERENCE_ANALYSIS_FAILED")
