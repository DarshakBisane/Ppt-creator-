"""Tests verifying canonical archetype mappings to Phase 6 LayoutRegistry."""

from backend.app.domain.enums import VisualType
from backend.app.layout.registry import default_layout_registry
from backend.app.visual_intelligence.archetype_map import (
    ARCHETYPE_MAPPINGS,
    get_archetype_descriptor,
)


def test_all_visual_types_have_registered_archetype_resolvers() -> None:
    for vtype, descriptor in ARCHETYPE_MAPPINGS.items():
        # Ensure preferred archetype is registered in layout engine
        resolver = default_layout_registry.get_resolver(descriptor.preferred_archetype)
        assert resolver is not None

        # Ensure fallback archetype is registered
        fallback_resolver = default_layout_registry.get_resolver(descriptor.fallback_archetype)
        assert fallback_resolver is not None


def test_get_archetype_descriptor_fallback() -> None:
    desc = get_archetype_descriptor(VisualType.TIMELINE)
    assert desc.preferred_archetype == "timeline"
    assert desc.fallback_archetype == "process_flow"
