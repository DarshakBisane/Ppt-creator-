"""Semantic content models for presentation elements."""

from typing import Literal
from pydantic import BaseModel, Field

from backend.app.domain.constants import (
    MAX_CARD_BODY_LENGTH,
    MAX_CARD_TITLE_LENGTH,
    MAX_KPI_LABEL_LENGTH,
    MAX_KPI_VALUE_LENGTH,
)


class TextContent(BaseModel):
    """Rich text block content."""

    text: str = Field(..., min_length=1)
    emphasis: bool = Field(default=False)
    variant: Literal["normal", "lead", "bullet", "quote", "callout"] = "normal"


class CardContent(BaseModel):
    """Structured card container content."""

    title: str = Field(..., min_length=1, max_length=MAX_CARD_TITLE_LENGTH)
    body: str = Field(..., max_length=MAX_CARD_BODY_LENGTH)
    metric: str | None = Field(default=None, max_length=50)
    supporting_text: str | None = Field(default=None, max_length=200)
    icon: str | None = Field(default=None, max_length=50)


class KPIContent(BaseModel):
    """Hero KPI metric block."""

    label: str = Field(..., min_length=1, max_length=MAX_KPI_LABEL_LENGTH)
    value: str = Field(..., min_length=1, max_length=MAX_KPI_VALUE_LENGTH)
    unit: str | None = Field(default=None, max_length=20)
    context: str | None = Field(default=None, max_length=150)
    trend: Literal["up", "down", "neutral"] | None = None


class IconContent(BaseModel):
    """Visual icon glyph specification."""

    icon_name: str = Field(..., min_length=1, max_length=50)
    label: str | None = Field(default=None, max_length=100)


class BadgeContent(BaseModel):
    """Semantic pill or category badge."""

    text: str = Field(..., min_length=1, max_length=50)
    variant: Literal["primary", "secondary", "accent", "success", "warning", "danger"] = "primary"
