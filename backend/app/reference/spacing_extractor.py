"""Spacing scale and layout density preferences extractor."""

import xml.etree.ElementTree as ET

from backend.app.domain.design_system import LayoutPreferences, SpacingScale
from backend.app.domain.enums import Density, WhitespacePreference
from backend.app.reference.inspector import SafePPTXPackage

PRESENTATION_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


class SpacingExtractor:
    """Infers content density and whitespace preference from reference presentation."""

    def __init__(self, package: SafePPTXPackage) -> None:
        self.package = package
        self.shapes_per_slide: list[int] = []

    def extract_preferences(self) -> tuple[SpacingScale, LayoutPreferences]:
        """Infer spacing scale and layout density preferences."""
        self._analyze_slide_densities()

        avg_shapes = (
            sum(self.shapes_per_slide) / len(self.shapes_per_slide)
            if self.shapes_per_slide
            else 6.0
        )

        if avg_shapes >= 12.0:
            density = Density.HIGH
            whitespace = WhitespacePreference.COMPACT
            scale = SpacingScale(xs=6, sm=12, md=18, lg=24, xl=36, xxl=48)
        elif avg_shapes <= 4.0:
            density = Density.LOW
            whitespace = WhitespacePreference.SPACIOUS
            scale = SpacingScale(xs=10, sm=20, md=30, lg=40, xl=60, xxl=80)
        else:
            density = Density.MEDIUM
            whitespace = WhitespacePreference.BALANCED
            scale = SpacingScale(xs=8, sm=16, md=24, lg=32, xl=48, xxl=64)

        prefs = LayoutPreferences(
            density=density,
            whitespace_preference=whitespace,
            preferred_columns=3,
        )

        return scale, prefs

    def _analyze_slide_densities(self) -> None:
        for part in self.package.get_slide_parts():
            try:
                root = self.package.read_xml(part)
                # Count shapes and groups
                shapes = root.findall(f".//{PRESENTATION_NS}sp")
                self.shapes_per_slide.append(len(shapes))
            except Exception:
                continue
