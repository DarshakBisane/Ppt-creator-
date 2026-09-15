"""Recurring visual motif and layout pattern detector for OpenXML presentations."""

import re
import xml.etree.ElementTree as ET
from collections import Counter

from backend.app.reference.inspector import SafePPTXPackage
from backend.app.reference.models import ExtractedMotif

DRAWING_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
PRESENTATION_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


class MotifDetector:
    """Detects visual layout motifs across slide OpenXML parts."""

    def __init__(self, package: SafePPTXPackage) -> None:
        self.package = package
        self.motif_counter: Counter[str] = Counter()

    def detect_motifs(self) -> list[ExtractedMotif]:
        """Detect and rank recurring visual motifs across all slides."""
        slide_parts = self.package.get_slide_parts()

        for part in slide_parts:
            try:
                root = self.package.read_xml(part)
                raw_xml = self.package.read_bytes(part).decode("utf-8", errors="ignore")

                # 1. Native Tables
                if "<a:tbl" in raw_xml or root.find(f".//{DRAWING_NS}tbl") is not None:
                    self.motif_counter["table"] += 1

                # 2. Native Charts
                if "chart" in raw_xml or "chart.xml" in raw_xml:
                    self.motif_counter["chart"] += 1

                # 3. Connectors & Workflows
                connectors = root.findall(f".//{PRESENTATION_NS}cxnSp")
                if connectors:
                    self.motif_counter["process_flow"] += 1
                    if len(connectors) >= 2:
                        self.motif_counter["timeline"] += 1

                # 4. Cards & Multi-Shape Groups
                shapes = root.findall(f".//{PRESENTATION_NS}sp")
                round_shapes = [s for s in shapes if "roundRect" in ET.tostring(s, encoding="unicode")]
                if len(round_shapes) >= 3 or len(shapes) >= 4:
                    self.motif_counter["card_grid"] += 1

                # 5. KPI Blocks (short stat strings like 99%, $10M, 100x)
                text_content = "".join(root.itertext())
                if re.search(r"(\b\d{1,3}%\b|\$\d+[\w.]*|\b\d+x\b|\b\d+\.\d+/\d+)", text_content):
                    self.motif_counter["kpi"] += 1

                # 6. Comparison / Split
                if len(shapes) == 2 or " vs " in text_content.lower() or "versus" in text_content.lower():
                    self.motif_counter["comparison"] += 1

            except Exception:
                continue

        # Synthesize ExtractedMotif objects
        results: list[ExtractedMotif] = []
        motif_archetype_map = {
            "card_grid": "card_grid",
            "kpi": "kpi",
            "table": "table",
            "chart": "column_chart",
            "timeline": "timeline",
            "process_flow": "process_flow",
            "comparison": "comparison",
        }

        total_slides = max(1, len(slide_parts))
        for motif, count in self.motif_counter.most_common():
            conf = min(0.95, round(0.5 + (count / total_slides) * 0.45, 2))
            results.append(
                ExtractedMotif(
                    motif_name=motif,
                    occurrences=count,
                    confidence=conf,
                    archetype_hint=motif_archetype_map.get(motif, motif),
                )
            )

        return results
