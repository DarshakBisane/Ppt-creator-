"""Tests for strict mathematical layout determinism."""

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.fake_provider import FakeAIProvider
from backend.app.layout.engine import LayoutEngine


def test_presentation_layout_determinism() -> None:
    """Verify that multiple consecutive layout resolutions produce identical geometry."""
    request = PresentationGenerationRequest(
        topic="Enterprise Artificial Intelligence Architecture",
        slide_count=7,
        purpose="Executive Board Review",
    )

    presentation = FakeAIProvider.create_deterministic_presentation(request)
    engine = LayoutEngine()

    # Run layout 10 times and assert exact equality
    first_result = engine.layout_presentation(presentation)

    for i in range(10):
        next_result = engine.layout_presentation(presentation)

        assert len(next_result.slides) == len(first_result.slides)

        for s_idx, (s_first, s_next) in enumerate(zip(first_result.slides, next_result.slides)):
            assert s_first.slide_id == s_next.slide_id
            assert s_first.header_rect == s_next.header_rect
            assert s_first.content_rect == s_next.content_rect
            assert len(s_first.elements) == len(s_next.elements)
            assert len(s_first.connectors) == len(s_next.connectors)

            # Check every element geometry down to exact pixel
            for e_idx, (e_first, e_next) in enumerate(zip(s_first.elements, s_next.elements)):
                assert e_first.id == e_next.id
                assert e_first.rect.x == e_next.rect.x
                assert e_first.rect.y == e_next.rect.y
                assert e_first.rect.width == e_next.rect.width
                assert e_first.rect.height == e_next.rect.height

                # Ports
                assert len(e_first.ports) == len(e_next.ports)
                for p_first, p_next in zip(e_first.ports, e_next.ports):
                    assert p_first.port_id == p_next.port_id
                    assert p_first.x == p_next.x
                    assert p_first.y == p_next.y

            # Connectors
            for c_first, c_next in zip(s_first.connectors, s_next.connectors):
                assert c_first.id == c_next.id
                assert c_first.start_x == c_next.start_x
                assert c_first.start_y == c_next.start_y
                assert c_first.end_x == c_next.end_x
                assert c_first.end_y == c_next.end_y
