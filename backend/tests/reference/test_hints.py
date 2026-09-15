"""Tests for visual layout motif and pattern detection."""

import pytest

from backend.app.reference.hints import MotifDetector
from backend.app.reference.inspector import SafePPTXPackage


def test_motif_detection_tables(light_theme_pptx_bytes: bytes) -> None:
    """Verify detection of table visual motif in light theme presentation."""
    pkg = SafePPTXPackage(light_theme_pptx_bytes)
    detector = MotifDetector(pkg)
    motifs = detector.detect_motifs()

    assert any(m.motif_name == "table" for m in motifs)
    pkg.close()


def test_motif_detection_kpi_and_cards(dark_theme_pptx_bytes: bytes) -> None:
    """Verify detection of KPI blocks and card grids in dark theme presentation."""
    pkg = SafePPTXPackage(dark_theme_pptx_bytes)
    detector = MotifDetector(pkg)
    motifs = detector.detect_motifs()

    assert any(m.motif_name in ("kpi", "card_grid") for m in motifs)
    pkg.close()
