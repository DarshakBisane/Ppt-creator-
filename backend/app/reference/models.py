"""Internal models for reference presentation analysis."""

from typing import Literal
from pydantic import BaseModel, Field


class ExtractedColor(BaseModel):
    """Extracted color token with frequency and confidence metrics."""

    hex_value: str
    role_hint: Literal["background", "surface", "primary", "secondary", "accent", "text_primary", "text_secondary", "border"]
    frequency: int = 1
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedFont(BaseModel):
    """Extracted font family with observed usage roles."""

    family: str
    is_major: bool = False
    is_minor: bool = False
    frequency: int = 1
    average_size_pt: float = 16.0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedMotif(BaseModel):
    """Observed recurring visual layout pattern."""

    motif_name: str
    occurrences: int = 1
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    archetype_hint: str


class ReferenceAnalysisSummary(BaseModel):
    """Metadata summary of the analyzed reference presentation."""

    slide_count: int
    is_dark_mode: bool
    dominant_background_hex: str
    dominant_primary_hex: str
    heading_font_family: str
    body_font_family: str
    inferred_density: str
    top_motifs: list[str] = Field(default_factory=list)
