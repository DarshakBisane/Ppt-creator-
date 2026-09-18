"""Deterministic spacing, distribution, alignment, and port calculation utilities."""

from backend.app.domain.design_system import DesignSystem
from backend.app.domain.enums import Density, WhitespacePreference
from backend.app.layout.constants import (
    DEFAULT_CARD_GAP,
    DEFAULT_CARD_PADDING,
    DEFAULT_COLUMN_GAP,
    DEFAULT_ROW_GAP,
    DEFAULT_SECTION_GAP,
    SAFE_MARGIN_X,
    SAFE_MARGIN_Y,
)
from backend.app.layout.models import ConnectorPort, PortSide, Rect


class SpacingContext:
    """Context holding resolved spacing parameters tailored to the active DesignSystem."""

    def __init__(self, design_system: DesignSystem | None = None) -> None:
        self.design_system = design_system or DesignSystem()
        self._resolve_tokens()

    def _resolve_tokens(self) -> None:
        density = self.design_system.layout_preferences.density
        whitespace = self.design_system.layout_preferences.whitespace_preference

        # Multiplier based on density
        density_scale = 1.0
        if density == Density.LOW:
            density_scale = 1.25
        elif density == Density.HIGH:
            density_scale = 0.8

        # Multiplier based on whitespace
        ws_scale = 1.0
        if whitespace == WhitespacePreference.SPACIOUS:
            ws_scale = 1.2
        elif whitespace == WhitespacePreference.COMPACT:
            ws_scale = 0.85

        combined_scale = density_scale * ws_scale

        self.margin_x = round(SAFE_MARGIN_X * ws_scale)
        self.margin_y = round(SAFE_MARGIN_Y * ws_scale)
        self.card_gap = max(12, round(DEFAULT_CARD_GAP * combined_scale))
        self.column_gap = max(16, round(DEFAULT_COLUMN_GAP * combined_scale))
        self.row_gap = max(12, round(DEFAULT_ROW_GAP * combined_scale))
        self.card_padding = max(12, round(self.design_system.geometry.card_padding * density_scale))
        self.section_gap = max(16, round(DEFAULT_SECTION_GAP * combined_scale))


def distribute_horizontal(total_width: int, count: int, gap: int) -> list[tuple[int, int]]:
    """Deterministically distribute a horizontal span across `count` elements.
    
    Returns a list of (start_offset, width) for each element without floating-point drift.
    """
    if count <= 0:
        return []
    if count == 1:
        return [(0, total_width)]

    total_gaps = gap * (count - 1)
    available_width = max(count, total_width - total_gaps)
    base_item_width = available_width // count
    remainder = available_width % count

    results: list[tuple[int, int]] = []
    current_x = 0
    for i in range(count):
        # Distribute remainder pixels deterministically across the first few slots
        extra = 1 if i < remainder else 0
        item_w = base_item_width + extra
        results.append((current_x, item_w))
        current_x += item_w + gap

    return results


def distribute_vertical(total_height: int, count: int, gap: int) -> list[tuple[int, int]]:
    """Deterministically distribute a vertical span across `count` elements.
    
    Returns a list of (start_offset, height) for each element without floating-point drift.
    """
    if count <= 0:
        return []
    if count == 1:
        return [(0, total_height)]

    total_gaps = gap * (count - 1)
    available_height = max(count, total_height - total_gaps)
    base_item_height = available_height // count
    remainder = available_height % count

    results: list[tuple[int, int]] = []
    current_y = 0
    for i in range(count):
        extra = 1 if i < remainder else 0
        item_h = base_item_height + extra
        results.append((current_y, item_h))
        current_y += item_h + gap

    return results


def calculate_card_row(bounds: Rect, count: int, gap: int) -> list[Rect]:
    """Split a bounding box into a single horizontal row of `count` cards (max 4)."""
    if count <= 0:
        return []
    # Hard clamp to max 4 cards for a single row to prevent narrow column squishing
    actual_count = min(count, 4)
    slices = distribute_horizontal(bounds.width, actual_count, gap)
    return [
        Rect(x=bounds.x + offset_x, y=bounds.y, width=w, height=bounds.height)
        for offset_x, w in slices
    ]


def calculate_multi_row_cards(
    bounds: Rect,
    count: int,
    max_cols: int = 4,
    col_gap: int = 16,
    row_gap: int = 14,
) -> list[Rect]:
    """Calculate balanced multi-row card rectangles for 1 to 8 items, capping at max_cols per row.
    
    Examples:
    - count = 5 -> Row 1 (3 items), Row 2 (2 items)
    - count = 6 -> Row 1 (3 items), Row 2 (3 items)
    - count = 7 -> Row 1 (4 items), Row 2 (3 items)
    - count = 8 -> Row 1 (4 items), Row 2 (4 items)
    """
    if count <= 0:
        return []
    if count <= max_cols:
        slices = distribute_horizontal(bounds.width, count, col_gap)
        return [
            Rect(x=bounds.x + offset_x, y=bounds.y, width=w, height=bounds.height)
            for offset_x, w in slices
        ]

    # Calculate number of rows
    num_rows = 2 if count <= (max_cols * 2) else ((count + max_cols - 1) // max_cols)
    row_slices = distribute_vertical(bounds.height, num_rows, row_gap)

    # Distribute count evenly across rows
    base_per_row = count // num_rows
    remainder = count % num_rows

    results: list[Rect] = []
    current_item_idx = 0

    for r_idx, (r_offset_y, r_h) in enumerate(row_slices):
        items_in_this_row = base_per_row + (1 if r_idx < remainder else 0)
        row_bounds_y = bounds.y + r_offset_y
        col_slices = distribute_horizontal(bounds.width, items_in_this_row, col_gap)

        for offset_x, w in col_slices:
            results.append(
                Rect(
                    x=bounds.x + offset_x,
                    y=row_bounds_y,
                    width=w,
                    height=r_h,
                )
            )
            current_item_idx += 1

    return results


def calculate_card_column(bounds: Rect, count: int, gap: int) -> list[Rect]:
    """Split a bounding box into a single vertical column of `count` cards."""
    slices = distribute_vertical(bounds.height, count, gap)
    return [
        Rect(x=bounds.x, y=bounds.y + offset_y, width=bounds.width, height=h)
        for offset_y, h in slices
    ]


def calculate_grid(bounds: Rect, cols: int, rows: int, col_gap: int, row_gap: int) -> list[list[Rect]]:
    """Calculate a 2D matrix of rectangular cells within bounds."""
    if cols <= 0 or rows <= 0:
        return []

    x_slices = distribute_horizontal(bounds.width, cols, col_gap)
    y_slices = distribute_vertical(bounds.height, rows, row_gap)

    grid: list[list[Rect]] = []
    for offset_y, cell_h in y_slices:
        row_rects: list[Rect] = []
        for offset_x, cell_w in x_slices:
            row_rects.append(
                Rect(
                    x=bounds.x + offset_x,
                    y=bounds.y + offset_y,
                    width=cell_w,
                    height=cell_h,
                )
            )
        grid.append(row_rects)

    return grid


def calculate_split(bounds: Rect, left_ratio: float, gap: int) -> tuple[Rect, Rect]:
    """Split bounds horizontally into left and right containers using ratio (e.g. 0.5 for 50/50, 0.6 for 60/40)."""
    left_ratio = max(0.1, min(0.9, left_ratio))
    available_width = max(2, bounds.width - gap)
    left_width = round(available_width * left_ratio)
    right_width = available_width - left_width

    left_rect = Rect(x=bounds.x, y=bounds.y, width=left_width, height=bounds.height)
    right_rect = Rect(
        x=bounds.x + left_width + gap,
        y=bounds.y,
        width=right_width,
        height=bounds.height,
    )
    return left_rect, right_rect


def generate_ports(element_id: str, rect: Rect) -> list[ConnectorPort]:
    """Generate standard deterministic attachment ports (top, bottom, left, right, center) for any Rect."""
    return [
        ConnectorPort(
            port_id=f"{element_id}_port_top",
            element_id=element_id,
            side="top",
            x=rect.center_x,
            y=rect.y,
        ),
        ConnectorPort(
            port_id=f"{element_id}_port_bottom",
            element_id=element_id,
            side="bottom",
            x=rect.center_x,
            y=rect.bottom,
        ),
        ConnectorPort(
            port_id=f"{element_id}_port_left",
            element_id=element_id,
            side="left",
            x=rect.x,
            y=rect.center_y,
        ),
        ConnectorPort(
            port_id=f"{element_id}_port_right",
            element_id=element_id,
            side="right",
            x=rect.right,
            y=rect.center_y,
        ),
        ConnectorPort(
            port_id=f"{element_id}_port_center",
            element_id=element_id,
            side="center",
            x=rect.center_x,
            y=rect.center_y,
        ),
    ]
