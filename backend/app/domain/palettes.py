"""Deterministic professional presentation color palette generator with light backgrounds."""

from enum import Enum
import hashlib
from typing import Literal

from backend.app.domain.design_system import ColorToken, Palette, TokenSource


class PaletteFamily(str, Enum):
    """Curated professional color palette families."""

    WARM_PROFESSIONAL = "warm_professional"
    GREEN_PROFESSIONAL = "green_professional"
    PURPLE_PROFESSIONAL = "purple_professional"
    RED_ACCENT = "red_accent"
    NEUTRAL_TECHNICAL = "neutral_technical"
    ACADEMIC = "academic"


PALETTE_DEFINITIONS: dict[PaletteFamily, dict[str, str]] = {
    PaletteFamily.WARM_PROFESSIONAL: {
        "background": "#FAF8F5",       # Warm cream / off-white
        "surface": "#FFFFFF",          # Crisp white card surface
        "primary": "#B45309",          # Terracotta amber
        "secondary": "#78350F",        # Deep bronze
        "accent": "#D97706",           # Muted gold
        "text_primary": "#1C1917",     # Warm dark charcoal
        "text_secondary": "#57534E",   # Stone gray
        "border": "#E7E5E4",           # Subtle warm border
        "success": "#15803D",
        "warning": "#B45309",
        "danger": "#B91C1C",
    },
    PaletteFamily.GREEN_PROFESSIONAL: {
        "background": "#F6F8F6",       # Sage off-white
        "surface": "#FFFFFF",          # Crisp white
        "primary": "#166534",          # Deep forest green
        "secondary": "#047857",        # Emerald green
        "accent": "#B45309",           # Warm gold accent
        "text_primary": "#141A16",     # Charcoal with green undertone
        "text_secondary": "#475569",   # Slate gray
        "border": "#E2E8F0",
        "success": "#166534",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    PaletteFamily.PURPLE_PROFESSIONAL: {
        "background": "#FAF9FD",       # Light lavender off-white
        "surface": "#FFFFFF",
        "primary": "#6D28D9",          # Deep royal purple
        "secondary": "#4F46E5",        # Indigo
        "accent": "#0891B2",           # Cyan teal contrast
        "text_primary": "#1E1B4B",     # Deep night navy
        "text_secondary": "#4B5563",
        "border": "#E5E7EB",
        "success": "#15803D",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    PaletteFamily.RED_ACCENT: {
        "background": "#FAF9F8",       # Warm off-white
        "surface": "#FFFFFF",
        "primary": "#9F1239",          # Burgundy / crimson
        "secondary": "#881337",        # Wine
        "accent": "#D97706",           # Warm amber
        "text_primary": "#18181B",     # Zinc charcoal
        "text_secondary": "#52525B",
        "border": "#E4E4E7",
        "success": "#15803D",
        "warning": "#D97706",
        "danger": "#9F1239",
    },
    PaletteFamily.NEUTRAL_TECHNICAL: {
        "background": "#F8FAFC",       # Slate off-white
        "surface": "#FFFFFF",          # Pure white card
        "primary": "#0F766E",          # Deep teal slate
        "secondary": "#1E293B",        # Graphite
        "accent": "#0284C7",           # Sky blue accent
        "text_primary": "#0F172A",     # Deep graphite slate
        "text_secondary": "#475569",   # Muted slate
        "border": "#E2E8F0",
        "success": "#0F766E",
        "warning": "#D97706",
        "danger": "#BE123C",
    },
    PaletteFamily.ACADEMIC: {
        "background": "#FDFBF7",       # Ivory parchment
        "surface": "#FFFFFF",
        "primary": "#7F1D1D",          # Deep academic maroon
        "secondary": "#854D0E",        # Antique bronze
        "accent": "#C2410C",           # Terracotta
        "text_primary": "#1C1917",     # Traditional rich black
        "text_secondary": "#57534E",   # Warm stone
        "border": "#E7E5E4",
        "success": "#15803D",
        "warning": "#B45309",
        "danger": "#7F1D1D",
    },
}


class ProfessionalPaletteGenerator:
    """Generates deterministic, domain-tailored professional color palettes with light backgrounds."""

    @classmethod
    def infer_family_from_topic(cls, topic: str, audience: str | None = None) -> PaletteFamily:
        """Deterministically infer the best palette family based on topic semantics."""
        t_lower = (topic + " " + (audience or "")).lower()

        if any(w in t_lower for w in ["academic", "research", "thesis", "history", "university", "paper", "literature", "education"]):
            return PaletteFamily.ACADEMIC

        if any(w in t_lower for w in ["green", "energy", "renewable", "climate", "nature", "sustainability", "eco", "agriculture", "health", "biology"]):
            return PaletteFamily.GREEN_PROFESSIONAL

        if any(w in t_lower for w in ["quantum", "ai", "machine learning", "neural", "deep learning", "creative", "media"]):
            return PaletteFamily.PURPLE_PROFESSIONAL

        if any(w in t_lower for w in ["risk", "incident", "threat", "emergency", "defense", "crisis", "sales pitch", "urgent"]):
            return PaletteFamily.RED_ACCENT

        if any(w in t_lower for w in ["business", "strategy", "finance", "banking", "investment", "executive", "market", "growth", "consulting"]):
            return PaletteFamily.WARM_PROFESSIONAL

        # Default for technical architecture, cybersecurity, infrastructure, systems
        return PaletteFamily.NEUTRAL_TECHNICAL

    @classmethod
    def create_palette(
        cls,
        family: PaletteFamily | str | None = None,
        topic: str | None = None,
        audience: str | None = None,
    ) -> Palette:
        """Create a complete Palette domain model for the chosen family."""
        if family is None and topic:
            fam = cls.infer_family_from_topic(topic, audience)
        elif isinstance(family, str):
            try:
                fam = PaletteFamily(family.lower().strip())
            except ValueError:
                fam = PaletteFamily.NEUTRAL_TECHNICAL
        elif isinstance(family, PaletteFamily):
            fam = family
        else:
            fam = PaletteFamily.NEUTRAL_TECHNICAL

        raw = PALETTE_DEFINITIONS.get(fam, PALETTE_DEFINITIONS[PaletteFamily.NEUTRAL_TECHNICAL])

        return Palette(
            background=ColorToken(value=raw["background"], source=TokenSource.DEFAULT),
            surface=ColorToken(value=raw["surface"], source=TokenSource.DEFAULT),
            primary=ColorToken(value=raw["primary"], source=TokenSource.DEFAULT),
            secondary=ColorToken(value=raw["secondary"], source=TokenSource.DEFAULT),
            accent=ColorToken(value=raw["accent"], source=TokenSource.DEFAULT),
            text_primary=ColorToken(value=raw["text_primary"], source=TokenSource.DEFAULT),
            text_secondary=ColorToken(value=raw["text_secondary"], source=TokenSource.DEFAULT),
            border=ColorToken(value=raw["border"], source=TokenSource.DEFAULT),
            success=ColorToken(value=raw["success"], source=TokenSource.DEFAULT),
            warning=ColorToken(value=raw["warning"], source=TokenSource.DEFAULT),
            danger=ColorToken(value=raw["danger"], source=TokenSource.DEFAULT),
        )


default_palette_generator = ProfessionalPaletteGenerator()
