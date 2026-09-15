"""Semantic element models representing slide content nodes."""

from typing import Literal
from pydantic import BaseModel, Field

from backend.app.domain.content import (
    BadgeContent,
    CardContent,
    IconContent,
    KPIContent,
    TextContent,
)
from backend.app.domain.enums import ElementType


class Element(BaseModel):
    """Semantic element on a slide without hardcoded physical coordinates."""

    id: str = Field(..., min_length=1, max_length=64, description="Unique element identifier")
    type: ElementType = Field(..., description="Semantic element type")
    role: str = Field(default="content", max_length=50, description="Functional role (e.g. title, body, card, stat)")
    importance: Literal["primary", "secondary", "accent", "background"] = Field(
        default="primary", description="Visual priority level for layout weight"
    )
    text_content: TextContent | None = None
    card_content: CardContent | None = None
    kpi_content: KPIContent | None = None
    icon_content: IconContent | None = None
    badge_content: BadgeContent | None = None
    children: list["Element"] | None = Field(default=None, description="Optional nested child elements")
