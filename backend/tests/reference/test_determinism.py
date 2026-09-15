"""Tests for strict deterministic behavior in reference extraction."""

import pytest

from backend.app.reference.analyzer import ReferencePPTAnalyzer


def test_reference_analyzer_determinism(dark_theme_pptx_bytes: bytes) -> None:
    """Verify that analyzing the same presentation bytes multiple times yields identical results."""
    analyzer = ReferencePPTAnalyzer()

    ctx1, ds1, sum1 = analyzer.analyze(dark_theme_pptx_bytes)

    for _ in range(5):
        ctx_next, ds_next, sum_next = analyzer.analyze(dark_theme_pptx_bytes)

        assert ctx1.model_dump_json() == ctx_next.model_dump_json()
        assert ds1.model_dump_json() == ds_next.model_dump_json()
        assert sum1.model_dump_json() == sum_next.model_dump_json()
