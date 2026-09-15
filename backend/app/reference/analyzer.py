"""Reference PPT Intelligence Analyzer orchestrator."""

from typing import BinaryIO

from backend.app.ai.context import DesignContext
from backend.app.domain.canvas import CanvasSpec
from backend.app.domain.design_system import DesignSystem
from backend.app.reference.color_extractor import ColorExtractor
from backend.app.reference.font_extractor import FontExtractor
from backend.app.reference.hints import MotifDetector
from backend.app.reference.inspector import SafePPTXPackage
from backend.app.reference.models import ReferenceAnalysisSummary
from backend.app.reference.shape_extractor import ShapeExtractor
from backend.app.reference.spacing_extractor import SpacingExtractor


class ReferencePPTAnalyzer:
    """Production Reference PPT Intelligence Analyzer.
    
    Extracts visual design language (palettes, typography hierarchies, shape styles,
    spacing preferences, and recurring motifs) from uploaded PowerPoint presentations.
    
    SECURITY GUARANTEE: Never extracts or leaks slide body text, titles, speaker notes,
    or proprietary text into the synthesized DesignSystem or DesignContext.
    """

    def analyze(
        self,
        source: bytes | str | BinaryIO,
    ) -> tuple[DesignContext, DesignSystem, ReferenceAnalysisSummary]:
        """Analyze a reference PowerPoint presentation and synthesize canonical design tokens.
        
        Returns:
            tuple[DesignContext, DesignSystem, ReferenceAnalysisSummary]
        """
        package = SafePPTXPackage(source)
        try:
            # 1. Color Palette Extraction
            color_extractor = ColorExtractor(package)
            palette, is_dark_mode = color_extractor.extract_palette()

            # 2. Typography Hierarchy Extraction
            font_extractor = FontExtractor(package)
            typography = font_extractor.extract_typography()

            # 3. Shape & Container Styling Extraction
            shape_extractor = ShapeExtractor(package)
            shape_style = shape_extractor.extract_shape_style()

            # 4. Spacing Scale & Density Preferences Extraction
            spacing_extractor = SpacingExtractor(package)
            spacing_scale, layout_prefs = spacing_extractor.extract_preferences()

            # 5. Visual Motif Detection
            motif_detector = MotifDetector(package)
            motifs = motif_detector.detect_motifs()
            archetype_hints = [m.archetype_hint for m in motifs[:5]]

            # 6. Synthesize Canonical DesignSystem
            design_system = DesignSystem(
                canvas=CanvasSpec(),
                palette=palette,
                typography=typography,
                geometry=shape_style,
                spacing=spacing_scale,
                layout_preferences=layout_prefs,
            )

            # 7. Synthesize Sanitized DesignContext for Phase 4 AI Orchestration
            style_name = "dark_tech" if is_dark_mode else "clean_editorial"
            design_context = DesignContext(
                design_system=design_system,
                style_name=style_name,
                archetype_hints=archetype_hints,
            )

            # 8. Construct Metadata Summary
            slide_count = len(package.get_slide_parts())
            summary = ReferenceAnalysisSummary(
                slide_count=slide_count,
                is_dark_mode=is_dark_mode,
                dominant_background_hex=palette.background.value,
                dominant_primary_hex=palette.primary.value,
                heading_font_family=typography.title.font_family,
                body_font_family=typography.body.font_family,
                inferred_density=layout_prefs.density.value,
                top_motifs=[m.motif_name for m in motifs[:5]],
            )

            return design_context, design_system, summary

        finally:
            package.close()

    def extract_design_context(self, source: bytes | str | BinaryIO) -> DesignContext:
        """Convenience method returning sanitized DesignContext."""
        ctx, _, _ = self.analyze(source)
        return ctx

    def extract_design_system(self, source: bytes | str | BinaryIO) -> DesignSystem:
        """Convenience method returning canonical DesignSystem."""
        _, ds, _ = self.analyze(source)
        return ds


# Global default analyzer instance
default_reference_analyzer = ReferencePPTAnalyzer()


def analyze_reference_presentation(
    source: bytes | str | BinaryIO,
) -> tuple[DesignContext, DesignSystem, ReferenceAnalysisSummary]:
    """Convenience helper to analyze a reference presentation."""
    return default_reference_analyzer.analyze(source)
