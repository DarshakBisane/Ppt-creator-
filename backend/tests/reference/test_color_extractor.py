"""Tests for color extraction, theme palette analysis, and dark/light classification."""

import pytest

from backend.app.domain.enums import TokenSource
from backend.app.reference.color_extractor import (
    ColorExtractor,
    calculate_luminance,
    normalize_hex,
)
from backend.app.reference.inspector import SafePPTXPackage


def test_normalize_hex_variations() -> None:
    """Verify hex string normalization."""
    assert normalize_hex("6366F1") == "#6366F1"
    assert normalize_hex("#6366f1") == "#6366F1"
    assert normalize_hex("FFF") == "#FFFFFF"
    assert normalize_hex("invalid") == "#1E293B"


def test_luminance_calculation() -> None:
    """Verify relative luminance calculation."""
    # Pure white = 1.0, Pure black = 0.0
    assert calculate_luminance("#FFFFFF") == pytest.approx(1.0, rel=1e-2)
    assert calculate_luminance("#000000") == pytest.approx(0.0, abs=1e-3)

    # Dark background < 0.35
    assert calculate_luminance("#0F172A") < 0.35


def test_dark_theme_color_extraction(dark_theme_pptx_bytes: bytes) -> None:
    """Verify extraction of dark mode palette tokens and confidence scores."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    extractor = ColorExtractor(pkg)
    palette, is_dark_mode = extractor.extract_palette()

    assert is_dark_mode is True
    assert palette.background.value == "#0F172A"
    assert palette.background.source == TokenSource.EXTRACTED
    assert palette.background.confidence >= 0.8

    # Text primary must be light color in dark mode
    assert calculate_luminance(palette.text_primary.value) > 0.5
    pkg.close()


def test_light_theme_color_extraction(light_theme_pptx_bytes: bytes) -> None:
    """Verify extraction of light mode palette tokens."""
    pkg = SafePPTXPackage(light_theme_pptx_bytes)
    extractor = ColorExtractor(pkg)
    palette, is_dark_mode = extractor.extract_palette()

    assert is_dark_mode is False
    assert palette.background.value == "#FFFFFF"
    assert palette.background.source == TokenSource.EXTRACTED

    # Text primary must be dark color in light mode
    assert calculate_luminance(palette.text_primary.value) < 0.35
    pkg.close()
