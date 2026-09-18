"""Tests for DesignSystem and style token models."""

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    ColorToken,
    Density,
    DesignSystem,
    Palette,
    ShapeStyle,
    SpacingScale,
    TokenSource,
    TypographyStyle,
    TypographySystem,
    WhitespacePreference,
)


def test_valid_color_token_hex_normalization() -> None:
    """Verify color token normalizes hex format and validates uppercase."""
    token1 = ColorToken(value="#1e293b", source=TokenSource.EXTRACTED, confidence=0.95)
    assert token1.value == "#1E293B"
    assert token1.source == TokenSource.EXTRACTED
    assert token1.confidence == 0.95

    # Auto-prefixes missing '#'
    token2 = ColorToken(value="6366f1")
    assert token2.value == "#6366F1"


def test_color_token_rejects_invalid_hex() -> None:
    """Verify invalid hex colors raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        ColorToken(value="not-a-color")
    assert "Invalid hex color format" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ColorToken(value="#GGGGGG")
    assert "Invalid hex color format" in str(exc.value)


def test_color_token_confidence_bounds() -> None:
    """Verify confidence must be in [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        ColorToken(value="#FFFFFF", confidence=1.5)

    with pytest.raises(ValidationError):
        ColorToken(value="#FFFFFF", confidence=-0.1)


def test_design_system_defaults() -> None:
    """Verify default design system initializes with robust tokens."""
    ds = DesignSystem()
    assert ds.canvas.width == 1920
    assert ds.canvas.height == 1080
    assert ds.palette.primary.value == "#0F766E"
    assert ds.typography.title.font_size == 32
    assert ds.geometry.corner_radius == 12
    assert ds.spacing.md == 24
    assert ds.layout_preferences.density == Density.MEDIUM
    assert ds.layout_preferences.whitespace_preference == WhitespacePreference.BALANCED
