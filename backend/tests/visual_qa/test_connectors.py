"""Unit tests for connector geometry, endpoint validation, and port snapping."""

from backend.app.domain.enums import ElementType
from backend.app.layout.models import ConnectorGeometry, ConnectorPort, ElementGeometry, Rect
from backend.app.layout.spacing import generate_ports
from backend.app.visual_qa.connectors import snap_connector_endpoints, validate_connectors
from backend.app.visual_qa.models import QAIssueType, QASeverity


def test_valid_connector_between_cards_passes() -> None:
    """A valid forward connector between card 1 and card 2 passes with 0 issues."""
    card_1_rect = Rect(x=100, y=200, width=400, height=300)
    card_2_rect = Rect(x=600, y=200, width=400, height=300)

    card_1 = ElementGeometry(
        id="step_1",
        semantic_type=ElementType.CARD,
        rect=card_1_rect,
        ports=generate_ports("step_1", card_1_rect),
    )
    card_2 = ElementGeometry(
        id="step_2",
        semantic_type=ElementType.CARD,
        rect=card_2_rect,
        ports=generate_ports("step_2", card_2_rect),
    )

    port_out = card_1.get_port("right")
    port_in = card_2.get_port("left")
    assert port_out is not None and port_in is not None

    conn = ConnectorGeometry(
        id="conn_1_2",
        start_port_id=port_out.port_id,
        end_port_id=port_in.port_id,
        start_x=port_out.x,
        start_y=port_out.y,
        end_x=port_in.x,
        end_y=port_in.y,
    )

    issues = validate_connectors([conn], [card_1, card_2], slide_id="s1")
    assert len(issues) == 0


def test_zero_length_connector_flagged() -> None:
    """A connector with start_x == end_x and start_y == end_y triggers CONNECTOR_INVALID ERROR."""
    conn = ConnectorGeometry(
        id="bad_conn",
        start_x=500,
        start_y=300,
        end_x=500,
        end_y=300,
    )
    issues = validate_connectors([conn], [], slide_id="s1")
    assert any(i.issue_type == QAIssueType.CONNECTOR_INVALID and i.severity == QASeverity.ERROR for i in issues)


def test_connector_port_snapping_repairs_offset() -> None:
    """A connector with coordinates slightly offset from ports snaps to the exact port coordinate."""
    card_rect = Rect(x=100, y=200, width=400, height=300)
    card = ElementGeometry(
        id="step_1",
        semantic_type=ElementType.CARD,
        rect=card_rect,
        ports=generate_ports("step_1", card_rect),
    )
    port_right = card.get_port("right")
    assert port_right is not None

    # Slightly offset start_x and start_y
    conn = ConnectorGeometry(
        id="offset_conn",
        start_port_id=port_right.port_id,
        start_x=port_right.x + 15,
        start_y=port_right.y - 10,
        end_x=1000,
        end_y=port_right.y,
    )

    repaired_conn, was_repaired = snap_connector_endpoints(conn, [card])
    assert was_repaired is True
    assert repaired_conn.start_x == port_right.x
    assert repaired_conn.start_y == port_right.y
