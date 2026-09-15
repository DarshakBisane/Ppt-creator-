"""Native PowerPoint connector rendering."""

from typing import Any
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.util import Pt

from backend.app.domain.design_system import DesignSystem
from backend.app.layout.constants import virtual_to_emu
from backend.app.layout.models import ConnectorGeometry
from backend.app.rendering.shapes import hex_to_rgb


def render_connector(
    slide_shape_tree: Any,
    conn: ConnectorGeometry,
    ds: DesignSystem,
) -> Any:
    """Render a native PowerPoint connector line/arrow between resolved ports."""
    start_x = virtual_to_emu(conn.start_x)
    start_y = virtual_to_emu(conn.start_y)
    end_x = virtual_to_emu(conn.end_x)
    end_y = virtual_to_emu(conn.end_y)

    connector_type = MSO_CONNECTOR.STRAIGHT
    if conn.connector_type == "elbow":
        connector_type = MSO_CONNECTOR.ELBOW
    elif conn.connector_type == "curved":
        connector_type = MSO_CONNECTOR.CURVE

    connector = slide_shape_tree.add_connector(
        connector_type,
        start_x,
        start_y,
        end_x,
        end_y,
    )

    color_hex = conn.color_token or ds.palette.primary.value
    connector.line.color.rgb = hex_to_rgb(color_hex)
    connector.line.width = Pt(conn.stroke_width)

    return connector
