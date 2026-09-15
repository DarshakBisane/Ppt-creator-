"""Deterministic layout engine exceptions."""


class LayoutEngineError(Exception):
    """Base exception for all layout engine failures."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnknownArchetypeError(LayoutEngineError):
    """Raised when an unrecognized visual archetype or layout key is requested."""


class LayoutConstraintError(LayoutEngineError):
    """Raised when geometric constraints cannot be satisfied."""


class GeometryValidationError(LayoutEngineError):
    """Raised when an element's resolved geometry violates safe boundaries or physical validity."""


class TextOverflowError(LayoutEngineError):
    """Raised when text content exceeds allowable container space even after reduction."""
