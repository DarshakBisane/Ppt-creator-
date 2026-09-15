"""Connector relationship validation, endpoint verification, and port snapping."""

import math
from backend.app.domain.enums import ElementType
from backend.app.layout.models import ConnectorGeometry, ConnectorPort, ElementGeometry, Rect
from backend.app.visual_qa.models import LayerCategory, QAIssue, QAIssueType, QASeverity
from backend.app.visual_qa.spatial import classify_layer


def find_element_by_port(port_id: str, elements: list[ElementGeometry]) -> tuple[ElementGeometry | None, ConnectorPort | None]:
    """Lookup parent element and port definition by port ID."""
    for elem in elements:
        for p in elem.ports:
            if p.port_id == port_id:
                return elem, p
    return None, None


def line_intersects_rect(x1: int, y1: int, x2: int, y2: int, rect: Rect) -> bool:
    """Return True if line segment (x1, y1)-(x2, y2) crosses strictly inside rect (inset by 4px)."""
    inner = rect.inset(4, 4)
    # Check if endpoints are inside
    if inner.contains_point(x1, y1) or inner.contains_point(x2, y2):
        return True

    # Simple bounding box check of line segment vs rect
    min_lx = min(x1, x2)
    max_lx = max(x1, x2)
    min_ly = min(y1, y2)
    max_ly = max(y1, y2)

    if max_lx < inner.x or min_lx > inner.right or max_ly < inner.y or min_ly > inner.bottom:
        return False

    return True


def snap_connector_endpoints(
    conn: ConnectorGeometry,
    elements: list[ElementGeometry],
) -> tuple[ConnectorGeometry, bool]:
    """Deterministically snap invalid or slightly offset connector endpoints to nearest element ports.
    
    Returns: (repaired_connector, was_repaired)
    """
    repaired = False
    elem_by_id: dict[str, ElementGeometry] = {e.id: e for e in elements}

    # Find closest source and target elements if not mapped by port ID
    start_elem, start_p = find_element_by_port(conn.start_port_id or "", elements)
    end_elem, end_p = find_element_by_port(conn.end_port_id or "", elements)

    # If no explicit port ID, find element whose rect is closest to start/end point
    if not start_elem:
        best_dist = 100.0  # Max snap distance
        for elem in elements:
            if elem.semantic_type in (ElementType.CARD, ElementType.SHAPE, ElementType.KPI):
                for p in elem.ports:
                    dist = math.hypot(conn.start_x - p.x, conn.start_y - p.y)
                    if dist < best_dist:
                        best_dist = dist
                        start_elem = elem
                        start_p = p

    if not end_elem:
        best_dist = 100.0  # Max snap distance
        for elem in elements:
            if elem.semantic_type in (ElementType.CARD, ElementType.SHAPE, ElementType.KPI):
                for p in elem.ports:
                    dist = math.hypot(conn.end_x - p.x, conn.end_y - p.y)
                    if dist < best_dist:
                        best_dist = dist
                        end_elem = elem
                        end_p = p

    new_start_x, new_start_y = conn.start_x, conn.start_y
    new_end_x, new_end_y = conn.end_x, conn.end_y
    new_start_port = conn.start_port_id
    new_end_port = conn.end_port_id

    if start_p:
        if conn.start_x != start_p.x or conn.start_y != start_p.y:
            new_start_x, new_start_y = start_p.x, start_p.y
            new_start_port = start_p.port_id
            repaired = True

    if end_p:
        if conn.end_x != end_p.x or conn.end_y != end_p.y:
            new_end_x, new_end_y = end_p.x, end_p.y
            new_end_port = end_p.port_id
            repaired = True

    updated_conn = ConnectorGeometry(
        id=conn.id,
        start_port_id=new_start_port,
        end_port_id=new_end_port,
        start_x=new_start_x,
        start_y=new_start_y,
        end_x=new_end_x,
        end_y=new_end_y,
        connector_type=conn.connector_type,
        label=conn.label,
        color_token=conn.color_token,
        stroke_width=conn.stroke_width,
    )

    return updated_conn, repaired


def validate_connectors(
    connectors: list[ConnectorGeometry],
    elements: list[ElementGeometry],
    slide_id: str,
    slide_index: int = 1,
) -> list[QAIssue]:
    """Validate that all connectors attach to valid elements and do not obscure content."""
    issues: list[QAIssue] = []
    sorted_conns = sorted(connectors, key=lambda c: (c.start_y, c.start_x, c.id))

    for conn in sorted_conns:
        # 1. Zero-length or negative connector
        length = math.hypot(conn.end_x - conn.start_x, conn.end_y - conn.start_y)
        if length <= 2.0:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.CONNECTOR_INVALID,
                    severity=QASeverity.ERROR,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=conn.id,
                    message=f"Connector '{conn.id}' has near-zero length ({length:.1f}px)",
                    measured_value=length,
                    expected_value="length > 10px",
                    correction_strategy="remove_or_reroute_connector",
                    is_correctable=True,
                )
            )
            continue

        # 2. Check endpoints attach to valid ports or elements
        start_elem, start_p = find_element_by_port(conn.start_port_id or "", elements)
        end_elem, end_p = find_element_by_port(conn.end_port_id or "", elements)

        if conn.start_port_id and not start_p:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.CONNECTOR_INVALID,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=conn.id,
                    message=f"Connector '{conn.id}' start_port_id '{conn.start_port_id}' does not exist",
                    correction_strategy="snap_to_nearest_port",
                    is_correctable=True,
                )
            )

        if conn.end_port_id and not end_p:
            issues.append(
                QAIssue(
                    issue_type=QAIssueType.CONNECTOR_INVALID,
                    severity=QASeverity.WARNING,
                    slide_id=slide_id,
                    slide_index=slide_index,
                    element_id=conn.id,
                    message=f"Connector '{conn.id}' end_port_id '{conn.end_port_id}' does not exist",
                    correction_strategy="snap_to_nearest_port",
                    is_correctable=True,
                )
            )

        # 3. Check if connector crosses through unrelated primary content elements
        for elem in elements:
            if elem.id in (getattr(start_elem, "id", None), getattr(end_elem, "id", None)):
                continue

            layer = classify_layer(elem)
            if layer == LayerCategory.CONTENT and elem.semantic_type in (ElementType.HEADING, ElementType.TEXT, ElementType.KPI):
                if line_intersects_rect(conn.start_x, conn.start_y, conn.end_x, conn.end_y, elem.rect):
                    issues.append(
                        QAIssue(
                            issue_type=QAIssueType.CONNECTOR_CONTENT_OVERLAP,
                            severity=QASeverity.WARNING,
                            slide_id=slide_id,
                            slide_index=slide_index,
                            element_id=conn.id,
                            related_element_ids=[elem.id],
                            message=f"Connector '{conn.id}' crosses over primary content in element '{elem.id}'",
                            correction_strategy="reroute_or_offset_connector",
                            is_correctable=True,
                        )
                    )

    return issues
