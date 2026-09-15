"""Text measurement, font metrics estimation, and responsive container fitting."""

import functools
from PIL import ImageFont

from backend.app.layout.constants import (
    MAX_CONTAINER_EXPANSION_RATIO,
    MIN_BODY_FONT_SIZE,
    MIN_CAPTION_FONT_SIZE,
)
from backend.app.layout.models import LayoutWarning, Rect


@functools.lru_cache(maxsize=128)
def _get_pil_font(font_family: str, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load and cache PIL font if available on OS, or return default bitmap font."""
    # Common system font filenames for Windows and Linux
    font_candidates = [
        f"{font_family}.ttf",
        f"{font_family.lower()}.ttf",
        "arial.ttf",
        "calibri.ttf",
        "DejaVuSans.ttf",
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, font_size)
        except Exception:
            continue
    return ImageFont.load_default()


def estimate_text_dimensions(
    text: str,
    font_size: int,
    max_width: int,
    line_height_multiplier: float = 1.3,
) -> tuple[int, int, int]:
    """Estimate rendered width, height, and line count for text wrapped within max_width.
    
    Returns: (measured_width, measured_height, line_count)
    """
    if not text:
        return 0, 0, 0

    # Average character width coefficient for standard sans-serif fonts
    # ~0.55 of font size per character in virtual points
    char_width = max(6, int(font_size * 0.52))
    line_height = max(14, int(font_size * line_height_multiplier))

    words = text.split()
    if not words:
        return 0, 0, 0

    lines: list[str] = []
    current_line: list[str] = []
    current_line_len = 0

    for word in words:
        word_len = len(word) * char_width
        space_len = char_width if current_line else 0
        if current_line and (current_line_len + space_len + word_len > max_width):
            lines.append(" ".join(current_line))
            current_line = [word]
            current_line_len = word_len
        else:
            current_line.append(word)
            current_line_len += space_len + word_len

    if current_line:
        lines.append(" ".join(current_line))

    line_count = max(1, len(lines))
    total_height = line_count * line_height
    max_line_width = min(max_width, max(len(l) * char_width for l in lines))

    return max_line_width, total_height, line_count


def fit_text_in_rect(
    text: str,
    target_rect: Rect,
    initial_font_size: int,
    min_font_size: int = MIN_BODY_FONT_SIZE,
    allow_expansion: bool = True,
    max_expansion_ratio: float = MAX_CONTAINER_EXPANSION_RATIO,
    element_id: str = "text_elem",
) -> tuple[Rect, int, list[LayoutWarning]]:
    """Fit text within target_rect adhering to the priority order:
    
    1. Expand container height up to max_expansion_ratio if allowed.
    2. Reduce font size gradually down to min_font_size.
    3. Generate a structured warning if text still exceeds container capacity.
    
    Returns: (fitted_rect, resolved_font_size, warnings)
    """
    warnings: list[LayoutWarning] = []
    current_font_size = initial_font_size
    current_rect = target_rect

    # Step 1: Initial measurement
    _, required_h, _ = estimate_text_dimensions(
        text=text,
        font_size=current_font_size,
        max_width=current_rect.width,
    )

    if required_h <= current_rect.height:
        return current_rect, current_font_size, warnings

    # Step 2: Try container expansion if allowed
    if allow_expansion:
        max_allowed_h = int(target_rect.height * (1.0 + max_expansion_ratio))
        if required_h <= max_allowed_h:
            expanded_rect = Rect(
                x=current_rect.x,
                y=current_rect.y,
                width=current_rect.width,
                height=required_h,
            )
            return expanded_rect, current_font_size, warnings
        else:
            # Expand to max allowed and continue with font reduction
            current_rect = Rect(
                x=current_rect.x,
                y=current_rect.y,
                width=current_rect.width,
                height=max_allowed_h,
            )

    # Step 3: Gradually reduce font size
    while current_font_size > min_font_size:
        current_font_size -= 1
        _, required_h, _ = estimate_text_dimensions(
            text=text,
            font_size=current_font_size,
            max_width=current_rect.width,
        )
        if required_h <= current_rect.height:
            return current_rect, current_font_size, warnings

    # Step 4: Minimum font reached, if still overflowing, log structured warning
    if required_h > current_rect.height:
        warnings.append(
            LayoutWarning(
                code="TEXT_OVERFLOW_WARNING",
                message=(
                    f"Text in element '{element_id}' requires {required_h}px height at {min_font_size}pt, "
                    f"exceeding available height {current_rect.height}px."
                ),
                slide_id="current",
                element_id=element_id,
                severity="warning",
            )
        )

    return current_rect, min_font_size, warnings
