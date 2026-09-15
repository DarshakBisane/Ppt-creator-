"""Deterministic Presentation Layout Engine."""

from backend.app.domain.design_system import DesignSystem
from backend.app.domain.presentation import Presentation, Slide
from backend.app.layout.models import (
    LayoutWarning,
    PresentationLayoutResult,
    SlideLayoutResult,
)
from backend.app.layout.registry import LayoutRegistry, default_layout_registry
from backend.app.layout.resolver import SlideLayoutResolver


class LayoutEngine:
    """Production Deterministic Layout Engine.
    
    Transforms semantic presentation domains and design tokens into mathematically
    precise physical coordinates on a 1920x1080 virtual canvas.
    """

    def __init__(self, registry: LayoutRegistry | None = None) -> None:
        self.registry = registry or default_layout_registry
        self.resolver = SlideLayoutResolver(self.registry)

    def layout_slide(
        self,
        slide: Slide,
        design_system: DesignSystem | None = None,
    ) -> SlideLayoutResult:
        """Resolve a single slide into concrete geometric positions."""
        return self.resolver.resolve_slide(slide, design_system)

    def layout_presentation(
        self,
        presentation: Presentation,
    ) -> PresentationLayoutResult:
        """Resolve an entire multi-slide presentation into a deterministic layout bundle."""
        ds = presentation.design_system or DesignSystem()
        slide_results: list[SlideLayoutResult] = []
        all_warnings: list[LayoutWarning] = []

        for slide in presentation.slides:
            res = self.layout_slide(slide, ds)
            slide_results.append(res)
            all_warnings.extend(res.warnings)

        return PresentationLayoutResult(
            presentation_title=presentation.metadata.title,
            slides=slide_results,
            warnings=all_warnings,
            canvas=ds.canvas,
        )


# Global layout engine instance
default_layout_engine = LayoutEngine()


def resolve_presentation_layout(presentation: Presentation) -> PresentationLayoutResult:
    """Convenience helper to resolve layout for a Presentation."""
    return default_layout_engine.layout_presentation(presentation)
