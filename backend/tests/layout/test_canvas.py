"""Tests for canonical 16:9 virtual canvas and centralized EMU conversion."""

import pytest

from backend.app.domain.canvas import CanvasSpec
from backend.app.layout.constants import (
    CANVAS_ASPECT_RATIO,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EMU_PER_VIRTUAL_UNIT,
    virtual_to_emu,
)
from backend.app.layout.models import Rect


def test_canonical_canvas_dimensions() -> None:
    """Verify standard 1920x1080 virtual canvas resolution."""
    assert CANVAS_WIDTH == 1920
    assert CANVAS_HEIGHT == 1080
    assert CANVAS_ASPECT_RATIO == "16:9"

    canvas = CanvasSpec()
    assert canvas.width == 1920
    assert canvas.height == 1080
    assert canvas.aspect_ratio == "16:9"
    assert canvas.orientation == "landscape"


def test_emu_conversion_factor() -> None:
    """Verify centralized EMU conversion factor (6350 EMU per virtual unit)."""
    assert EMU_PER_VIRTUAL_UNIT == 6350

    # 1920 virtual units * 6350 = 12,192,000 EMU
    # 12,192,000 EMU / 914,400 EMU per inch = 13.333333 inches (standard 16:9 widescreen PPTX width)
    assert virtual_to_emu(CANVAS_WIDTH) == 12192000

    # 1080 virtual units * 6350 = 6,858,000 EMU
    # 6,858,000 EMU / 914,400 EMU per inch = 7.5 inches (standard 16:9 widescreen PPTX height)
    assert virtual_to_emu(CANVAS_HEIGHT) == 6858000


def test_rect_emu_conversion() -> None:
    """Verify Rect conversion to EMU coordinates."""
    rect = Rect(x=100, y=200, width=500, height=300)
    x_emu, y_emu, w_emu, h_emu = rect.to_emu()

    assert x_emu == 635000
    assert y_emu == 1270000
    assert w_emu == 3175000
    assert h_emu == 1905000
