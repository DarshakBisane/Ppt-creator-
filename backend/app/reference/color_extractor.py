"""Color and theme palette extractor for OpenXML presentations."""

import re
import xml.etree.ElementTree as ET
from collections import Counter

from backend.app.domain.design_system import ColorToken, Palette
from backend.app.domain.enums import TokenSource
from backend.app.reference.inspector import SafePPTXPackage

DRAWING_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PRESENTATION_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def normalize_hex(raw_hex: str) -> str:
    """Normalize raw hex string into canonical #RRGGBB uppercase format."""
    clean = raw_hex.strip().lstrip("#").upper()
    if len(clean) == 3:
        clean = "".join([c * 2 for c in clean])
    if len(clean) == 8:
        clean = clean[:6]
    if len(clean) != 6 or not re.match(r"^[0-9A-F]{6}$", clean):
        return "#1E293B"  # Safe default fallback
    return f"#{clean}"


def calculate_luminance(hex_str: str) -> float:
    """Calculate relative perceived luminance (0.0 to 1.0) according to ITU-R BT.709."""
    hex_clean = hex_str.lstrip("#")
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class ColorExtractor:
    """Extracts theme color schemes, slide fills, and synthesizes a canonical Palette."""

    def __init__(self, package: SafePPTXPackage) -> None:
        self.package = package
        self.theme_colors: dict[str, str] = {}
        self.color_counter: Counter[str] = Counter()
        self.bg_color_counter: Counter[str] = Counter()
        self.text_color_counter: Counter[str] = Counter()

    def extract_palette(self) -> tuple[Palette, bool]:
        """Extract and synthesize canonical semantic Palette and is_dark_mode flag."""
        self._harvest_theme_colors()
        self._harvest_slide_colors()

        return self._synthesize_palette()

    def _harvest_theme_colors(self) -> None:
        theme_parts = self.package.get_theme_parts()
        if not theme_parts:
            return

        try:
            theme_root = self.package.read_xml(theme_parts[0])
            clr_scheme = theme_root.find(f".//{DRAWING_NS}clrScheme")
            if clr_scheme is None:
                return

            for child in clr_scheme:
                tag = child.tag.replace(DRAWING_NS, "")
                # Find srgbClr or sysClr
                srgb = child.find(f"{DRAWING_NS}srgbClr")
                if srgb is not None and "val" in srgb.attrib:
                    self.theme_colors[tag] = normalize_hex(srgb.attrib["val"])
                else:
                    sys_clr = child.find(f"{DRAWING_NS}sysClr")
                    if sys_clr is not None and "lastClr" in sys_clr.attrib:
                        self.theme_colors[tag] = normalize_hex(sys_clr.attrib["lastClr"])
        except Exception:
            # Theme extraction failed gracefully, fallback to slide fills
            pass

    def _harvest_slide_colors(self) -> None:
        all_parts = self.package.get_slide_master_parts() + self.package.get_slide_parts()

        for part_name in all_parts:
            try:
                root = self.package.read_xml(part_name)

                # 1. Native background fills (<p:bg>)
                for bg in root.findall(f".//{PRESENTATION_NS}bg"):
                    for srgb in bg.findall(f".//{DRAWING_NS}srgbClr"):
                        val = srgb.attrib.get("val")
                        if val:
                            hex_c = normalize_hex(val)
                            self.bg_color_counter[hex_c] += 10
                            self.color_counter[hex_c] += 10

                # 2. Shape properties (<p:sp>)
                for sp in root.findall(f".//{PRESENTATION_NS}sp"):
                    sp_pr = sp.find(f"{PRESENTATION_NS}spPr")
                    if sp_pr is None:
                        continue

                    # Check for full-bleed background shape
                    xfrm = sp_pr.find(f"{DRAWING_NS}xfrm")
                    is_bg_shape = False
                    if xfrm is not None:
                        off = xfrm.find(f"{DRAWING_NS}off")
                        ext = xfrm.find(f"{DRAWING_NS}ext")
                        if off is not None and ext is not None:
                            x = int(off.attrib.get("x", "0"))
                            y = int(off.attrib.get("y", "0"))
                            cx = int(ext.attrib.get("cx", "0"))
                            cy = int(ext.attrib.get("cy", "0"))
                            # If shape starts at origin and covers most of slide canvas
                            if x == 0 and y == 0 and cx >= 5000000 and cy >= 3000000:
                                is_bg_shape = True

                    for srgb in sp_pr.findall(f".//{DRAWING_NS}srgbClr"):
                        val = srgb.attrib.get("val")
                        if val:
                            hex_c = normalize_hex(val)
                            if is_bg_shape:
                                self.bg_color_counter[hex_c] += 10
                            self.color_counter[hex_c] += 1

                # 3. Text run solid fills (<a:rPr>)
                for r_pr in root.findall(f".//{DRAWING_NS}rPr"):
                    for srgb in r_pr.findall(f".//{DRAWING_NS}srgbClr"):
                        val = srgb.attrib.get("val")
                        if val:
                            hex_c = normalize_hex(val)
                            self.text_color_counter[hex_c] += 1
                            self.color_counter[hex_c] += 1

            except Exception:
                continue

    def _synthesize_palette(self) -> tuple[Palette, bool]:
        # 1. Determine Background Color
        if self.bg_color_counter:
            dominant_bg = self.bg_color_counter.most_common(1)[0][0]
            bg_conf = 0.95
        elif "lt1" in self.theme_colors and "dk1" in self.theme_colors:
            # Default PowerPoint theme has lt1 as background and dk1 as text
            dominant_bg = self.theme_colors["lt1"]
            bg_conf = 0.85
        else:
            dominant_bg = "#FFFFFF"
            bg_conf = 0.60

        bg_lum = calculate_luminance(dominant_bg)
        is_dark_mode = bg_lum < 0.45

        # 2. Surface Color
        if is_dark_mode:
            # Look for slightly lighter surface color in extracted colors
            surface_candidate = self._find_surface_color(is_dark=True, bg_lum=bg_lum)
            surface_hex = surface_candidate or self.theme_colors.get("dk2") or "#1E293B"
        else:
            # Look for slightly darker surface color in extracted colors
            surface_candidate = self._find_surface_color(is_dark=False, bg_lum=bg_lum)
            surface_hex = surface_candidate or self.theme_colors.get("lt2") or "#F1F5F9"

        # 3. Accent Colors (from accent1..accent6 or top non-bg colors)
        acc1 = self._resolve_accent(1, exclude=[dominant_bg, surface_hex], fallback="#6366F1")
        acc2 = self._resolve_accent(2, exclude=[dominant_bg, surface_hex, acc1], fallback="#8B5CF6")
        acc3 = self._resolve_accent(3, exclude=[dominant_bg, surface_hex, acc1, acc2], fallback="#06B6D4")

        # 4. Text Colors
        if is_dark_mode:
            text_p = self.theme_colors.get("lt1", "#F8FAFC")
            if calculate_luminance(text_p) < 0.4:
                text_p = "#F8FAFC"
            text_s = self.theme_colors.get("lt2", "#94A3B8")
            if calculate_luminance(text_s) < 0.3:
                text_s = "#94A3B8"
        else:
            text_p = self.theme_colors.get("dk1", "#0F172A")
            if calculate_luminance(text_p) > 0.5:
                text_p = "#0F172A"
            text_s = self.theme_colors.get("dk2", "#475569")
            if calculate_luminance(text_s) > 0.6:
                text_s = "#475569"

        palette = Palette(
            background=ColorToken(value=dominant_bg, source=TokenSource.EXTRACTED, confidence=bg_conf),
            surface=ColorToken(value=surface_hex, source=TokenSource.EXTRACTED, confidence=0.85),
            primary=ColorToken(value=acc1, source=TokenSource.EXTRACTED, confidence=0.90 if "accent1" in self.theme_colors else 0.75),
            secondary=ColorToken(value=acc2, source=TokenSource.EXTRACTED, confidence=0.85 if "accent2" in self.theme_colors else 0.70),
            accent=ColorToken(value=acc3, source=TokenSource.EXTRACTED, confidence=0.85 if "accent3" in self.theme_colors else 0.70),
            text_primary=ColorToken(value=text_p, source=TokenSource.EXTRACTED, confidence=0.90),
            text_secondary=ColorToken(value=text_s, source=TokenSource.EXTRACTED, confidence=0.85),
        )

        return palette, is_dark_mode

    def _find_surface_color(self, is_dark: bool, bg_lum: float) -> str | None:
        for color, _ in self.color_counter.most_common(20):
            lum = calculate_luminance(color)
            if is_dark:
                if bg_lum < lum <= 0.35:
                    return color
            else:
                if 0.70 <= lum < bg_lum:
                    return color
        return None

    def _resolve_accent(self, accent_num: int, exclude: list[str], fallback: str) -> str:
        key = f"accent{accent_num}"
        if key in self.theme_colors:
            val = self.theme_colors[key]
            if val not in exclude:
                return val
        return self._find_best_accent(exclude=exclude, fallback=fallback)

    def _find_best_accent(self, exclude: list[str], fallback: str) -> str:
        exclude_set = {normalize_hex(c) for c in exclude if c}
        for color, _ in self.color_counter.most_common(20):
            if color not in exclude_set:
                lum = calculate_luminance(color)
                # Avoid extreme near-black or near-white as vibrant accents
                if 0.15 <= lum <= 0.85:
                    return color
        return fallback
