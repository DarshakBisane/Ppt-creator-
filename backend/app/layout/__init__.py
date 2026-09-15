"""Deterministic Presentation Layout Engine Package."""

from backend.app.layout.constants import (
    CANVAS_ASPECT_RATIO,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EMU_PER_VIRTUAL_UNIT,
    virtual_to_emu,
)
from backend.app.layout.engine import (
    LayoutEngine,
    default_layout_engine,
    resolve_presentation_layout,
)
from backend.app.layout.exceptions import (
    GeometryValidationError,
    LayoutConstraintError,
    LayoutEngineError,
    TextOverflowError,
    UnknownArchetypeError,
)
from backend.app.layout.models import (
    ConnectorGeometry,
    ConnectorPort,
    ConnectorType,
    ElementGeometry,
    LayoutWarning,
    PortSide,
    PresentationLayoutResult,
    Rect,
    SlideLayoutResult,
)
from backend.app.layout.registry import LayoutRegistry, default_layout_registry
from backend.app.layout.resolver import SlideLayoutResolver

__all__ = [
    # Constants & Conversion
    "CANVAS_ASPECT_RATIO",
    "CANVAS_HEIGHT",
    "CANVAS_WIDTH",
    "EMU_PER_VIRTUAL_UNIT",
    "virtual_to_emu",
    # Engine & Resolvers
    "LayoutEngine",
    "default_layout_engine",
    "resolve_presentation_layout",
    "SlideLayoutResolver",
    "LayoutRegistry",
    "default_layout_registry",
    # Models
    "Rect",
    "PortSide",
    "ConnectorPort",
    "ConnectorType",
    "ConnectorGeometry",
    "ElementGeometry",
    "LayoutWarning",
    "SlideLayoutResult",
    "PresentationLayoutResult",
    # Exceptions
    "LayoutEngineError",
    "UnknownArchetypeError",
    "LayoutConstraintError",
    "GeometryValidationError",
    "TextOverflowError",
]
