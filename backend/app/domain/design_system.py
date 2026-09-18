"""Design system and style token models."""

import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.enums import (
    Density,
    TokenSource,
    WhitespacePreference,
)

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class ColorToken(BaseModel):
    """Normalized color token with extraction provenance and confidence score."""

    value: str = Field(..., description="Hex color code (e.g. #1E293B)")
    source: TokenSource = Field(
        default=TokenSource.DEFAULT,
        description="Source of this token (default, extracted, inferred, user, fallback)",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for inferred/extracted tokens (0.0 to 1.0)",
    )

    @field_validator("value")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        clean = v.strip()
        if not clean.startswith("#"):
            clean = f"#{clean}"
        if not HEX_COLOR_REGEX.match(clean):
            raise ValueError(f"Invalid hex color format: {v}. Must be valid hex like #FFFFFF or #1E293B")
        return clean.upper()


class Palette(BaseModel):
    """Semantic color palette with light-theme defaults."""

    background: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#F8FAFC", source=TokenSource.DEFAULT)
    )
    surface: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#FFFFFF", source=TokenSource.DEFAULT)
    )
    primary: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#0F766E", source=TokenSource.DEFAULT)
    )
    secondary: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#1E293B", source=TokenSource.DEFAULT)
    )
    accent: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#0284C7", source=TokenSource.DEFAULT)
    )
    text_primary: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#0F172A", source=TokenSource.DEFAULT)
    )
    text_secondary: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#475569", source=TokenSource.DEFAULT)
    )
    border: ColorToken = Field(
        default_factory=lambda: ColorToken(value="#E2E8F0", source=TokenSource.DEFAULT)
    )
    success: ColorToken | None = None
    warning: ColorToken | None = None
    danger: ColorToken | None = None


class TypographyStyle(BaseModel):
    """Typography style specification."""

    font_family: str = Field(default="Calibri", description="Font family name (e.g. Calibri, Arial, Georgia)")
    font_size: int = Field(..., ge=1, description="Font size in points")
    font_weight: Literal["normal", "medium", "semibold", "bold", "extrabold"] = Field(
        default="normal"
    )
    line_height: float = Field(default=1.2, ge=0.8, le=2.5)
    letter_spacing: float = Field(default=0.0)


class TypographySystem(BaseModel):
    """Complete typography hierarchy."""

    display: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=40, font_weight="bold")
    )
    title: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=32, font_weight="bold")
    )
    heading: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=20, font_weight="semibold")
    )
    body: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=15, font_weight="normal")
    )
    label: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=12, font_weight="medium")
    )
    caption: TypographyStyle = Field(
        default_factory=lambda: TypographyStyle(font_family="Calibri", font_size=11, font_weight="normal")
    )



class ShapeStyle(BaseModel):
    """Geometry and card styling tokens."""

    corner_radius: int = Field(default=12, ge=0, le=50, description="Corner radius in virtual points")
    border_width: int = Field(default=1, ge=0, le=10, description="Border stroke width")
    shadow_style: Literal["none", "subtle", "medium", "elevated"] = "subtle"
    card_padding: int = Field(default=24, ge=4, le=80, description="Inner card padding in points")


class SpacingScale(BaseModel):
    """Spacing scale tokens in points."""

    xs: int = Field(default=8, ge=0)
    sm: int = Field(default=16, ge=0)
    md: int = Field(default=24, ge=0)
    lg: int = Field(default=32, ge=0)
    xl: int = Field(default=48, ge=0)
    xxl: int = Field(default=64, ge=0)


class LayoutPreferences(BaseModel):
    """Semantic layout hints for the deterministic engine."""

    density: Density = Field(default=Density.MEDIUM)
    whitespace_preference: WhitespacePreference = Field(default=WhitespacePreference.BALANCED)
    preferred_columns: int = Field(default=3, ge=1, le=6)


class DesignSystem(BaseModel):
    """Canonical Design System model acting as the visual contract."""

    canvas: CanvasSpec = Field(default_factory=CanvasSpec)
    palette: Palette = Field(default_factory=Palette)
    typography: TypographySystem = Field(default_factory=TypographySystem)
    geometry: ShapeStyle = Field(default_factory=ShapeStyle)
    spacing: SpacingScale = Field(default_factory=SpacingScale)
    layout_preferences: LayoutPreferences = Field(default_factory=LayoutPreferences)
