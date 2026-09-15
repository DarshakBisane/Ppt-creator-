"""Typography hierarchy and font extractor for OpenXML presentations."""

import xml.etree.ElementTree as ET
from collections import Counter

from backend.app.domain.design_system import TypographyStyle, TypographySystem
from backend.app.reference.inspector import SafePPTXPackage

DRAWING_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


class FontExtractor:
    """Extracts font families and sizing hierarchies from theme and slide XML."""

    def __init__(self, package: SafePPTXPackage) -> None:
        self.package = package
        self.major_font: str | None = None
        self.minor_font: str | None = None
        self.font_counter: Counter[str] = Counter()
        self.heading_font_counter: Counter[str] = Counter()
        self.body_font_counter: Counter[str] = Counter()
        self.size_counter: Counter[int] = Counter()

    def extract_typography(self) -> TypographySystem:
        """Extract and synthesize canonical TypographySystem."""
        self._harvest_theme_fonts()
        self._harvest_slide_fonts()

        return self._synthesize_typography()

    def _harvest_theme_fonts(self) -> None:
        theme_parts = self.package.get_theme_parts()
        if not theme_parts:
            return

        try:
            theme_root = self.package.read_xml(theme_parts[0])
            font_scheme = theme_root.find(f".//{DRAWING_NS}fontScheme")
            if font_scheme is None:
                return

            major = font_scheme.find(f"{DRAWING_NS}majorFont/{DRAWING_NS}latin")
            if major is not None and "typeface" in major.attrib and major.attrib["typeface"].strip():
                self.major_font = major.attrib["typeface"].strip()

            minor = font_scheme.find(f"{DRAWING_NS}minorFont/{DRAWING_NS}latin")
            if minor is not None and "typeface" in minor.attrib and minor.attrib["typeface"].strip():
                self.minor_font = minor.attrib["typeface"].strip()
        except Exception:
            pass

    def _harvest_slide_fonts(self) -> None:
        for part in self.package.get_slide_parts():
            try:
                root = self.package.read_xml(part)

                # Search all run properties with font size and latin typeface
                for r_pr in root.findall(f".//{DRAWING_NS}rPr"):
                    # Check size
                    sz_pt: int | None = None
                    sz_str = r_pr.attrib.get("sz")
                    if sz_str and sz_str.isdigit():
                        sz_val = int(sz_str) // 100
                        if 8 <= sz_val <= 96:
                            sz_pt = sz_val
                            self.size_counter[sz_pt] += 1

                    # Check typeface
                    latin = r_pr.find(f"{DRAWING_NS}latin")
                    if latin is not None:
                        face = latin.attrib.get("typeface")
                        if face and face.strip() and not face.startswith("+"):
                            clean_face = face.strip()
                            self.font_counter[clean_face] += 1
                            if sz_pt is not None:
                                if sz_pt >= 20:
                                    self.heading_font_counter[clean_face] += 1
                                else:
                                    self.body_font_counter[clean_face] += 1

                # Also search all bare latin elements not in rPr
                for latin in root.findall(f".//{DRAWING_NS}latin"):
                    face = latin.attrib.get("typeface")
                    if face and face.strip() and not face.startswith("+"):
                        clean_face = face.strip()
                        if clean_face not in self.font_counter:
                            self.font_counter[clean_face] += 1

            except Exception:
                continue

    def _synthesize_typography(self) -> TypographySystem:
        # Determine heading font: slide heading font -> overall slide font -> theme major font -> fallback
        if self.heading_font_counter:
            heading_font = self.heading_font_counter.most_common(1)[0][0]
        elif self.font_counter:
            heading_font = self.font_counter.most_common(1)[0][0]
        elif self.major_font:
            heading_font = self.major_font
        else:
            heading_font = "Outfit"

        # Determine body font: slide body font -> secondary slide font -> theme minor font -> fallback
        if self.body_font_counter:
            body_font = self.body_font_counter.most_common(1)[0][0]
        elif len(self.font_counter) > 1:
            body_font = self.font_counter.most_common(2)[1][0]
        elif self.font_counter:
            body_font = self.font_counter.most_common(1)[0][0]
        elif self.minor_font:
            body_font = self.minor_font
        else:
            body_font = "Inter"

        # Infer typical sizes from distribution
        heading_sizes = [sz for sz in self.size_counter if sz >= 20]
        typical_heading_sz = max(heading_sizes) if heading_sizes else 32

        body_sizes = [sz for sz in self.size_counter if 12 <= sz <= 18]
        typical_body_sz = min(body_sizes) if body_sizes else 16

        return TypographySystem(
            display=TypographyStyle(
                font_family=heading_font,
                font_size=min(48, typical_heading_sz + 8),
                font_weight="extrabold",
            ),
            title=TypographyStyle(
                font_family=heading_font,
                font_size=min(40, typical_heading_sz),
                font_weight="bold",
            ),
            heading=TypographyStyle(
                font_family=heading_font,
                font_size=max(20, min(28, typical_heading_sz - 8)),
                font_weight="semibold",
            ),
            body=TypographyStyle(
                font_family=body_font,
                font_size=typical_body_sz,
                font_weight="normal",
            ),
            caption=TypographyStyle(
                font_family=body_font,
                font_size=max(11, typical_body_sz - 4),
                font_weight="normal",
            ),
            label=TypographyStyle(
                font_family=body_font,
                font_size=max(12, typical_body_sz - 2),
                font_weight="medium",
            ),
        )
