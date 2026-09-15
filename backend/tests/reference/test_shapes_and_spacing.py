"""Tests for shape style, corner radius, and layout spacing extraction."""

import pytest

from backend.app.domain.enums import Density
from backend.app.reference.inspector import SafePPTXPackage
from backend.app.reference.shape_extractor import ShapeExtractor
from backend.app.reference.spacing_extractor import SpacingExtractor


def test_rounded_shape_extraction(dark_theme_pptx_bytes: bytes) -> None:
    """Verify corner radius inference from rounded rectangle shapes."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    shape_extractor = ShapeExtractor(pkg)
    style = shape_extractor.extract_shape_style()

    assert style.corner_radius >= 8
    assert style.border_width >= 1
    pkg.close()


def test_spacing_and_density_extraction(dark_theme_pptx_bytes: bytes) -> None:
    """Verify spacing and density preference inference."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    spacing_extractor = SpacingExtractor(pkg)
    scale, prefs = spacing_extractor.extract_preferences()

    assert prefs.density in (Density.LOW, Density.MEDIUM, Density.HIGH)
    assert scale.md > scale.sm > scale.xs
    pkg.close()
