"""Deterministic semantic classifier analyzing slide content, narrative intent, and data signals."""

import re
from backend.app.domain.enums import NarrativeRole
from backend.app.domain.presentation import Slide
from backend.app.visual_intelligence.models import SemanticCategory, SemanticSignal


# Regex pattern sets for multi-signal detection
YEAR_REGEX = re.compile(r"\b(19\d\d|20\d\d)\b")
QUARTER_REGEX = re.compile(r"\b(Q[1-4]|H[1-2])\s*(20\d\d|\d\d)?\b", re.IGNORECASE)
DATE_MONTH_REGEX = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(20\d\d|\d\d)?\b", re.IGNORECASE)
QUANT_METRIC_REGEX = re.compile(r"(\b\d+(\.\d+)?%\b|\$\d+[\w.]*|€\d+[\w.]*|\b\d+[\w.]*\s*(million|billion|M|B|k|K|x)\b|\b\d+\s*to\s*\d+\b)", re.IGNORECASE)
STEP_NUMBER_REGEX = re.compile(r"\b(step\s*\d+|phase\s*\d+|stage\s*\d+|1st|2nd|3rd|4th|5th)\b", re.IGNORECASE)
VS_REGEX = re.compile(r"(\bvs\.?\b|\bversus\b|\bbefore\s+(and|vs\.?)\s+after\b|\bpros\s+(and|vs\.?)\s+cons\b|\boption\s+[A-Z]\b)", re.IGNORECASE)
ARROW_FLOW_REGEX = re.compile(r"(->|-->|=>|→|⟶|➜|⇒)")
QUOTE_MARK_REGEX = re.compile(r"[\"“][^\"”]{15,}[\"”]")

# Keyword dictionaries mapped to SemanticCategory
KEYWORD_SIGNALS: dict[SemanticCategory, list[str]] = {
    SemanticCategory.TEMPORAL: [
        "timeline", "milestone", "milestones", "history", "evolution", "chronology",
        "roadmap", "horizon", "past", "future", "anniversary", "origins",
        "q1", "q2", "q3", "q4", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
    ],
    SemanticCategory.SEQUENTIAL: [
        "step", "steps", "first", "second", "third", "next", "then", "finally",
        "procedure", "pipeline", "workflow", "lifecycle", "stages of", "process",
        "methodology", "execution plan", "onboarding flow", "funnel", "cycle",
    ],
    SemanticCategory.HIERARCHICAL: [
        "hierarchy", "hierarchical", "parent", "child", "reporting structure", "org chart",
        "organizational", "tree", "tier 1", "tier 2", "tier 3", "sub-categories",
        "breakdown structure", "levels", "cascading",
    ],
    SemanticCategory.COMPARATIVE: [
        "versus", "comparison", "compare", "trade-offs", "pros and cons",
        "advantages", "disadvantages", "option a", "option b", "competitor",
        "pricing plans", "alternative", "differences", "before vs after",
    ],
    SemanticCategory.QUANTITATIVE: [
        "revenue", "profit", "ebitda", "cagr", "retention", "churn", "growth rate",
        "metrics", "kpi", "roi", "arr", "mrr", "conversion rate", "statistics",
        "percentage", "quarterly earnings", "annual revenue", "headcount", "valuation",
    ],
    SemanticCategory.RELATIONAL: [
        "architecture", "system layers", "microservices", "api gateway", "frontend",
        "backend", "database", "infrastructure", "cloud stack", "components",
        "data flow", "data pipeline", "orchestration", "tech stack", "service bus",
    ],
    SemanticCategory.TABULAR: [
        "table", "specifications", "feature matrix", "feature list", "checklist",
        "breakdown by dimension", "matrix of", "attribute comparison", "record",
    ],
    SemanticCategory.KEY_STATEMENT: [
        "mission", "vision", "our belief", "core belief", "guiding principle",
        "testimonial", "quote by", "ceo statement", "manifesto", "callout",
    ],
}

# Role affinity mappings
ROLE_AFFINITY: dict[NarrativeRole, SemanticCategory] = {
    NarrativeRole.TITLE: SemanticCategory.KEY_STATEMENT,
    NarrativeRole.CONTEXT: SemanticCategory.CATEGORICAL,
    NarrativeRole.PROBLEM: SemanticCategory.KEY_STATEMENT,
    NarrativeRole.INSIGHT: SemanticCategory.KEY_STATEMENT,
    NarrativeRole.PROCESS: SemanticCategory.SEQUENTIAL,
    NarrativeRole.TIMELINE: SemanticCategory.TEMPORAL,
    NarrativeRole.COMPARISON: SemanticCategory.COMPARATIVE,
    NarrativeRole.EVIDENCE: SemanticCategory.QUANTITATIVE,
    NarrativeRole.SOLUTION: SemanticCategory.CATEGORICAL,
    NarrativeRole.ARCHITECTURE: SemanticCategory.RELATIONAL,
    NarrativeRole.CASE_STUDY: SemanticCategory.CATEGORICAL,
    NarrativeRole.SUMMARY: SemanticCategory.CATEGORICAL,
    NarrativeRole.CONCLUSION: SemanticCategory.KEY_STATEMENT,
    NarrativeRole.CALL_TO_ACTION: SemanticCategory.KEY_STATEMENT,
}


class ContentSemanticClassifier:
    """Classifies slide narrative and text content into weighted semantic categories."""

    def classify_slide(self, slide: Slide) -> SemanticSignal:
        """Analyze a slide and return structured semantic signals."""
        scores: dict[SemanticCategory, float] = {cat: 0.0 for cat in SemanticCategory}
        evidence: list[str] = []

        # 1. Harvest text content from slide
        title_text = slide.title.strip()
        subtitle_text = slide.subtitle.strip() if slide.subtitle else ""
        
        body_texts: list[str] = []
        for elem in slide.elements:
            if elem.text_content:
                body_texts.append(elem.text_content.text)
            if elem.card_content:
                body_texts.append(elem.card_content.title)
                body_texts.append(elem.card_content.body)
            if elem.kpi_content:
                body_texts.append(elem.kpi_content.value)
                body_texts.append(elem.kpi_content.label)

        all_text = f"{title_text} {subtitle_text} {' '.join(body_texts)}".strip()
        all_text_lower = all_text.lower()
        title_lower = title_text.lower()

        # 2. Check for Specific Regex Signals
        has_dates = bool(YEAR_REGEX.search(all_text) or QUARTER_REGEX.search(all_text) or DATE_MONTH_REGEX.search(all_text))
        has_quant = bool(QUANT_METRIC_REGEX.search(all_text))
        has_steps = bool(STEP_NUMBER_REGEX.search(all_text) or ARROW_FLOW_REGEX.search(all_text))
        has_comp = bool(VS_REGEX.search(all_text) or "comparison" in title_lower or "versus" in title_lower or " vs " in title_lower)
        has_quote = bool(QUOTE_MARK_REGEX.search(all_text))
        has_arch = bool(
            not has_comp
            and ("architecture" in all_text_lower or "layer" in all_text_lower or "stack" in all_text_lower)
            and ("database" in all_text_lower or "api" in all_text_lower or "service" in all_text_lower or "system" in all_text_lower)
        )

        # 3. Apply Keyword Scoring
        for cat, kw_list in KEYWORD_SIGNALS.items():
            for kw in kw_list:
                # Title matches have high weight (2.5)
                if kw in title_lower:
                    scores[cat] += 2.5
                    evidence.append(f"Title keyword: '{kw}' -> {cat.value}")
                elif kw in all_text_lower:
                    scores[cat] += 1.0
                    evidence.append(f"Body keyword: '{kw}' -> {cat.value}")

        # 4. Regex Multi-Signal Bonuses
        if has_dates:
            scores[SemanticCategory.TEMPORAL] += 3.0
            evidence.append("Detected explicit dates/years/quarters -> TEMPORAL")

        if has_steps:
            scores[SemanticCategory.SEQUENTIAL] += 3.0
            evidence.append("Detected sequential step markers / flow arrows -> SEQUENTIAL")

        if has_comp:
            scores[SemanticCategory.COMPARATIVE] += 6.0
            evidence.append("Detected 'vs' / comparison / before-after marker -> COMPARATIVE")

        if has_quote:
            scores[SemanticCategory.KEY_STATEMENT] += 3.0
            evidence.append("Detected quote marks / statement -> KEY_STATEMENT")

        if has_arch:
            scores[SemanticCategory.RELATIONAL] += 4.5
            evidence.append("Detected multi-tier system architecture components -> RELATIONAL")

        if has_quant:
            scores[SemanticCategory.QUANTITATIVE] += 3.0
            evidence.append("Detected quantitative figures / currency / metrics -> QUANTITATIVE")

        # 5. Existing VisualPlan / Data Payload Signals
        if slide.visual_plan:
            vp = slide.visual_plan
            if vp.timeline_data and len(vp.timeline_data.milestones) >= 2:
                scores[SemanticCategory.TEMPORAL] += 5.0
                has_dates = True
            if vp.process_flow_data and len(vp.process_flow_data.steps) >= 2:
                scores[SemanticCategory.SEQUENTIAL] += 5.0
                has_steps = True
            if vp.chart_data:
                scores[SemanticCategory.QUANTITATIVE] += 5.0
                has_quant = True
            if vp.table_data and len(vp.table_data.rows) >= 1:
                scores[SemanticCategory.TABULAR] += 5.0

        # 6. Narrative Role Affinity Boost
        role_cat = ROLE_AFFINITY.get(slide.narrative_role)
        if role_cat:
            scores[role_cat] += 2.0
            evidence.append(f"Narrative role '{slide.narrative_role.value}' affinity -> {role_cat.value}")

        # 7. Default Categorical Baseline
        scores[SemanticCategory.CATEGORICAL] += 1.0

        # 8. Negative Signal Adjustments (Crucial Rules)
        # If content has "stages of development" or sequential steps without numbers, penalize QUANTITATIVE
        if has_steps and not has_quant:
            scores[SemanticCategory.QUANTITATIVE] = max(0.0, scores[SemanticCategory.QUANTITATIVE] - 3.0)

        # If temporal keywords exist WITH quantitative metrics (e.g. "Revenue 2020-2025: 10M to 50M"), boost QUANTITATIVE
        if has_dates and has_quant:
            scores[SemanticCategory.QUANTITATIVE] += 2.5

        # 9. Resolve Primary Category & Confidence
        sorted_cats = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_cat, top_score = sorted_cats[0]
        second_score = sorted_cats[1][1] if len(sorted_cats) > 1 else 0.0

        # Calculate confidence
        if top_score <= 1.0:
            primary_cat = SemanticCategory.CATEGORICAL
            confidence = 0.50
        else:
            primary_cat = top_cat
            confidence = min(0.98, round(0.55 + ((top_score - second_score) / (top_score + 1.0)) * 0.40, 2))

        # Detect entity counts (cards, list items, steps)
        detected_entity_count = max(len(slide.elements), len(body_texts), 3)

        return SemanticSignal(
            primary_category=primary_cat,
            confidence=confidence,
            category_scores=scores,
            evidence=evidence[:10],
            has_quantitative_data=has_quant,
            has_explicit_dates=has_dates,
            has_sequential_steps=has_steps,
            has_entity_comparison=has_comp,
            has_system_components=has_arch,
            detected_entity_count=detected_entity_count,
        )
