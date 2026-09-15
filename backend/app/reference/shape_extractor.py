"""Shape style and geometry extractor for OpenXML presentations."""

import xml.etree.ElementTree as ET
from collections import Counter

from backend.app.domain.design_system import ShapeStyle
from backend.app.reference.inspector import SafePPTXPackage

DRAWING_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


class ShapeExtractor:
    """Extracts shape geometry preferences, corner radii, and stroke styling."""

    def __init__(self, package: SafePPTXPackage) -> None:
        self.package = package
        self.geom_counter: Counter[str] = Counter()
        self.stroke_widths: list[int] = []

    def extract_shape_style(self) -> ShapeStyle:
        """Extract and synthesize canonical ShapeStyle."""
        self._harvest_shape_properties()

        # 1. Corner radius inference
        round_rect_count = self.geom_counter.get("roundRect", 0)
        rect_count = self.geom_counter.get("rect", 0)
        total_boxes = round_rect_count + rect_count

        if total_boxes > 0 and (round_rect_count / total_boxes) >= 0.35:
            corner_radius = 12
        elif total_boxes > 0 and round_rect_count > 0:
            corner_radius = 8
        else:
            corner_radius = 0

        # 2. Border width inference
        if self.stroke_widths:
            avg_width_emu = sum(self.stroke_widths) / len(self.stroke_widths)
            border_pt = max(1, min(4, round(avg_width_emu / 12700)))
        else:
            border_pt = 1

        return ShapeStyle(
            corner_radius=corner_radius,
            border_width=border_pt,
            shadow_style="subtle" if round_rect_count > 0 else "none",
            card_padding=24,
        )

    def _harvest_shape_properties(self) -> None:
        for part in self.package.get_slide_parts():
            try:
                root = self.package.read_xml(part)

                # Preset geometries
                for geom in root.findall(f".//{DRAWING_NS}prstGeom"):
                    prst = geom.attrib.get("prst")
                    if prst:
                        self.geom_counter[prst] += 1

                # Line stroke widths
                for ln in root.findall(f".//{DRAWING_NS}ln"):
                    w_str = ln.attrib.get("w")
                    if w_str and w_str.isdigit():
                        self.stroke_widths.append(int(w_str))
            except Exception:
                continue
