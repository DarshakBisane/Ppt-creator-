"""Tests verifying mathematical determinism and stability of visual selections."""

from backend.app.domain.elements import CardContent, Element
from backend.app.domain.enums import ElementType, NarrativeRole
from backend.app.domain.presentation import Slide
from backend.app.visual_intelligence.selector import SemanticVisualSelector


def test_visual_selection_determinism(process_slide: Slide, timeline_slide: Slide) -> None:
    selector = SemanticVisualSelector()

    # Run decision 10 times and assert identical outputs
    d1 = selector.select_visual_for_slide(process_slide)
    for _ in range(10):
        d_repeat = selector.select_visual_for_slide(process_slide)
        assert d_repeat.selected_visual_type == d1.selected_visual_type
        assert d_repeat.selected_archetype == d1.selected_archetype
        assert d_repeat.confidence == d1.confidence
        assert d_repeat.rationale == d1.rationale

    t1 = selector.select_visual_for_slide(timeline_slide)
    for _ in range(10):
        t_repeat = selector.select_visual_for_slide(timeline_slide)
        assert t_repeat.selected_visual_type == t1.selected_visual_type
        assert t_repeat.selected_archetype == t1.selected_archetype
