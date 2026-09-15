"""Tests for typography hierarchy and font extraction."""

import pytest

from backend.app.reference.font_extractor import FontExtractor
from backend.app.reference.inspector import SafePPTXPackage


def test_font_extraction_from_dark_fixture(dark_theme_pptx_bytes: bytes) -> None:
    """Verify font extraction resolves observed typeface and hierarchy."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    extractor = FontExtractor(pkg)
    typo = extractor.extract_typography()

    assert typo.title.font_family == "Outfit"
    assert typo.display.font_size > typo.title.font_size
    assert typo.title.font_size > typo.heading.font_size
    assert typo.heading.font_size > typo.body.font_size
    assert typo.body.font_size > typo.caption.font_size
    pkg.close()


def test_font_extraction_from_light_fixture(light_theme_pptx_bytes: bytes) -> None:
    """Verify font extraction on Arial light theme presentation."""
    pkg = SafePPTXPackage(light_theme_pptx_bytes)
    extractor = FontExtractor(pkg)
    typo = extractor.extract_typography()

    assert typo.title.font_family == "Arial"
    assert typo.body.font_size == 16
    pkg.close()
