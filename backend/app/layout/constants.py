"""Constants and centralized conversion factors for deterministic layout calculations."""

# Canonical 16:9 Virtual Canvas Units (Abstract virtual coordinates, NOT PPT points)
CANVAS_WIDTH: int = 1920
CANVAS_HEIGHT: int = 1080
CANVAS_ASPECT_RATIO: str = "16:9"

# Centralized EMU Conversion
# 1920 * 6350 = 12,192,000 EMU (13.333 inches)
# 1080 * 6350 = 6,858,000 EMU (7.5 inches)
EMU_PER_VIRTUAL_UNIT: int = 6350


def virtual_to_emu(val: float | int) -> int:
    """Centralized conversion from virtual units to PowerPoint EMUs."""
    return round(float(val) * EMU_PER_VIRTUAL_UNIT)


# Safe Canvas Margin Defaults (Virtual Units)
SAFE_MARGIN_X: int = 100
SAFE_MARGIN_Y: int = 70

# Slide Layout Regions
HEADER_TOP: int = 70
HEADER_HEIGHT: int = 110
CONTENT_TOP: int = 195
CONTENT_BOTTOM: int = 1010
CONTENT_WIDTH: int = CANVAS_WIDTH - (SAFE_MARGIN_X * 2)  # 1720
CONTENT_HEIGHT: int = CONTENT_BOTTOM - CONTENT_TOP  # 815

# Default Spacing and Gaps
DEFAULT_CARD_GAP: int = 24
DEFAULT_COLUMN_GAP: int = 32
DEFAULT_ROW_GAP: int = 24
DEFAULT_CARD_PADDING: int = 24
DEFAULT_SECTION_GAP: int = 32

# Text Constraints & Fitting Thresholds
MIN_BODY_FONT_SIZE: int = 14
MIN_CAPTION_FONT_SIZE: int = 11
MAX_CONTAINER_EXPANSION_RATIO: float = 0.15  # Up to 15% expansion into available whitespace
