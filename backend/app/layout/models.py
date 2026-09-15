"""Deterministic geometric layout models and container hierarchy specifications."""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.enums import Alignment, ElementType, NarrativeRole, VisualType
from backend.app.layout.constants import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    virtual_to_emu,
)


class Rect(BaseModel):
    """Deterministic bounding box in 16:9 virtual canvas units."""

    x: int = Field(..., description="Top-left X coordinate in virtual units")
    y: int = Field(..., description="Top-left Y coordinate in virtual units")
    width: int = Field(..., gt=0, description="Width in virtual units")
    height: int = Field(..., gt=0, description="Height in virtual units")

    @property
    def right(self) -> int:
        """Right boundary X coordinate."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Bottom boundary Y coordinate."""
        return self.y + self.height

    @property
    def center_x(self) -> int:
        """Center X coordinate."""
        return self.x + (self.width // 2)

    @property
    def center_y(self) -> int:
        """Center Y coordinate."""
        return self.y + (self.height // 2)

    def contains_point(self, px: int, py: int) -> bool:
        """Return True if point (px, py) is strictly inside or on rect boundary."""
        return self.x <= px <= self.right and self.y <= py <= self.bottom

    def contains_rect(self, other: "Rect") -> bool:
        """Return True if other rect is completely contained within this rect."""
        return (
            self.x <= other.x
            and self.y <= other.y
            and other.right <= self.right
            and other.bottom <= self.bottom
        )

    def intersects(self, other: "Rect") -> bool:
        """Return True if this rect overlaps with another rect."""
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )

    def inset(self, dx: int, dy: int) -> "Rect":
        """Return a new rect shrunken inward by dx horizontally and dy vertically."""
        new_w = max(1, self.width - (2 * dx))
        new_h = max(1, self.height - (2 * dy))
        return Rect(x=self.x + dx, y=self.y + dy, width=new_w, height=new_h)

    def offset(self, dx: int, dy: int) -> "Rect":
        """Return a new rect shifted by dx horizontally and dy vertically."""
        return Rect(x=self.x + dx, y=self.y + dy, width=self.width, height=self.height)

    def to_emu(self) -> tuple[int, int, int, int]:
        """Convert virtual coordinates to PowerPoint EMUs (x_emu, y_emu, w_emu, h_emu)."""
        return (
            virtual_to_emu(self.x),
            virtual_to_emu(self.y),
            virtual_to_emu(self.width),
            virtual_to_emu(self.height),
        )


PortSide = Literal["top", "bottom", "left", "right", "center"]


class ConnectorPort(BaseModel):
    """Deterministic attachment point on an element border for connectors."""

    port_id: str = Field(..., description="Unique port identifier")
    element_id: str = Field(..., description="Parent element identifier")
    side: PortSide = Field(..., description="Container side")
    x: int = Field(..., description="Absolute canvas X position")
    y: int = Field(..., description="Absolute canvas Y position")


ConnectorType = Literal["line", "arrow", "curved", "elbow"]


class ConnectorGeometry(BaseModel):
    """Geometric path for connectors between semantic elements."""

    id: str = Field(..., description="Unique connector identifier")
    start_port_id: str | None = None
    end_port_id: str | None = None
    start_x: int = Field(..., description="Start X in virtual units")
    start_y: int = Field(..., description="Start Y in virtual units")
    end_x: int = Field(..., description="End X in virtual units")
    end_y: int = Field(..., description="End Y in virtual units")
    connector_type: ConnectorType = Field(default="arrow")
    label: str | None = None
    color_token: str | None = None
    stroke_width: int = Field(default=2, ge=1, le=10)


class LayoutWarning(BaseModel):
    """Structured layout warning describing boundary adjustments or tight fitting."""

    code: str = Field(..., description="Machine-readable warning code")
    message: str = Field(..., description="Human-readable explanation")
    slide_id: str = Field(..., description="Slide identifier")
    element_id: str | None = None
    severity: Literal["info", "warning", "error"] = Field(default="warning")


class ElementGeometry(BaseModel):
    """Resolved physical geometry for a semantic element on a slide."""

    id: str = Field(..., description="Unique element identifier")
    semantic_type: ElementType = Field(..., description="Domain element type")
    rect: Rect = Field(..., description="Resolved bounding box")
    parent_id: str | None = Field(default=None, description="Container parent element ID")
    z_index: int = Field(default=0, description="Stacking layer order")
    alignment: Alignment = Field(default=Alignment.LEFT)
    ports: list[ConnectorPort] = Field(default_factory=list)
    role: str = Field(default="content")
    importance: str = Field(default="primary")
    style_hints: dict[str, Any] = Field(default_factory=dict)
    content_data: Any | None = None

    def get_port(self, side: PortSide) -> ConnectorPort | None:
        """Lookup port by side."""
        for p in self.ports:
            if p.side == side:
                return p
        return None


class SlideLayoutResult(BaseModel):
    """Complete resolved layout for a single slide."""

    slide_id: str
    slide_number: int
    visual_type: VisualType
    narrative_role: NarrativeRole
    canvas: CanvasSpec = Field(default_factory=CanvasSpec)
    header_rect: Rect | None = None
    content_rect: Rect
    elements: list[ElementGeometry] = Field(default_factory=list)
    connectors: list[ConnectorGeometry] = Field(default_factory=list)
    warnings: list[LayoutWarning] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_element_ids(self) -> "SlideLayoutResult":
        seen: set[str] = set()
        for elem in self.elements:
            if elem.id in seen:
                raise ValueError(f"Duplicate element geometry ID '{elem.id}' in slide {self.slide_id}")
            seen.add(elem.id)
        return self


class PresentationLayoutResult(BaseModel):
    """Complete resolved layout bundle for an entire presentation."""

    presentation_title: str
    slides: list[SlideLayoutResult] = Field(..., min_length=1)
    warnings: list[LayoutWarning] = Field(default_factory=list)
    canvas: CanvasSpec = Field(default_factory=CanvasSpec)
