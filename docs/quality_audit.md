# Phase 1–12 System Quality Audit & Root Cause Analysis

## Executive Summary
This quality audit evaluates the end-to-end presentation generation pipeline across all 12 implemented phases. The current system is **functionally stable, architecturally sound, and technically correct**, with robust spatial layout computation, 3-pass geometric QA, and native PowerPoint OpenXML rendering.

However, the resulting presentations currently feel like **automated bullet-point summaries rather than executive-level presentations designed by seasoned consultants or technical architects**. This document analyzes the exact points where presentation quality is lost and outlines our architectural remediation strategy.

---

## Direct Audit Questions & Answers

### 1. Why are generated slides currently weak?
Generated slides are weak primarily because the generation pipeline operates in a **single-shot, unguided manner**:
- Gemini is given a raw user topic string and immediately asked to generate an entire 10-slide JSON deck in one shot.
- Without a preceding narrative planning stage, the AI defaults to dictionary-definition bullet points ("What is X?", "Features of X", "Benefits of X").
- There is no audience-specific framing, no analytical depth, no takeaway insights, and no storytelling arc.

### 2. Is the problem content planning?
**Yes, significantly.** 
- There is currently no pre-generation content planning stage.
- The AI does not define the presentation's core hypothesis, narrative strategy (e.g., Executive Problem-Solution, Technical Architecture Flow, Academic Discovery, or Analytical Case Study), or slide-by-slide storyline before drafting slide text.
- Every slide is generated in isolation without answering: *"Why does this slide exist?"* and *"What is the singular takeaway message the audience must remember?"*

### 3. Is the problem Gemini prompting?
**Yes, substantially.**
- The current prompt instructions in `backend/app/ai/prompts.py` focus primarily on JSON schema compliance and generic category definitions (e.g., "Processes -> process_flow", "Trends -> line_chart").
- The system instructions lack persona guidance (Lead Presentation Strategist & Information Designer), do not enforce message-driven titles (e.g., prohibiting "Benefits of AI" and requiring "AI reduces decision latency by automating risk scoring"), and do not specify target information densities or takeaway structures.

### 4. Is the problem slide narrative?
**Yes.**
- Presentations currently lack narrative coherence across the slide deck.
- The slides read as disconnected topical cards rather than an intentional story with tension, context, technical depth, empirical evidence, strategic choices, and actionable conclusions.

### 5. Is the problem visual selection?
**Partially.**
- The Semantic Visual Intelligence engine (Phase 8: `backend/app/visual_intelligence/`) has powerful rule scoring and classifiers for timelines, process flows, KPI dashboards, and comparisons.
- However, when the upstream AI generates generic bullet points in `elements`, the classifier receives weak semantic signals and frequently defaults to `CARD_GRID`.
- Furthermore, there was no deck-level visual budget preventing back-to-back card grids.

### 6. Is the problem layout?
**No.**
- The Phase 6 deterministic layout engine (`backend/app/layout/`) and SpacingContext are robust, calculating precise 1920x1080 coordinates, container paddings, card distributions, and connector ports.
- Layout archetypes (Hero, Two-Column, KPIDashboard, Timeline, ProcessFlow, Architecture, Comparison, Chart, Matrix, Table) render accurately.
- However, layouts can be enriched to display structured takeaways, subtitles, and insight callouts with higher visual polish.

### 7. Is the problem insufficient content?
**Yes.**
- The AI planner generates superficial, high-level bullets (e.g., "Faster processing", "Better efficiency", "Reduced cost") without measurable evidence, concrete implementation mechanisms, architectural tradeoffs, or domain-specific nuances.

### 8. Is the problem renderer limitations?
**No.**
- The Phase 5 PowerPoint renderer (`backend/app/rendering/`) natively renders editable PowerPoint OpenXML shapes, tables, charts, text frames, and connector lines with custom hex colors and typography.
- The renderer is fully capable of rendering executive-level layouts.

### 9. Is the problem lack of iterative generation/QA?
**Yes, for Content QA.**
- Phase 9 (`backend/app/visual_qa/`) executes a 3-pass spatial and geometric QA loop (detecting bounds overflow, collisions, text overflow, and container margins).
- However, there is **zero Content QA** in the system. The pipeline had no deterministic validation to catch generic titles, repetitive points, shallow bullets, card grid saturation, or missing takeaways before rendering.

### 10. Which modules should be modified or added?
The following modules must be enhanced or added:
1. **[NEW] `backend/app/ai/narrative.py`**: Presentation story arc templates (Business/Executive, Technical/Architecture, Academic/Educational, Research/Analytical).
2. **[NEW] `backend/app/ai/planner.py`**: Multi-stage presentation strategist that understands topic, detects audience/objective, selects narrative strategy, creates slide outline with visual intent, and plans rich content.
3. **[MODIFY] `backend/app/ai/prompts.py`**: Overhauled system instructions with executive consultant persona, message-driven title rules, information density targets, and anti-hallucination rules.
4. **[MODIFY] `backend/app/ai/gemini_provider.py`**: Integrated multi-stage planning and structured recovery.
5. **[MODIFY] `backend/app/ai/fake_provider.py`**: High-quality deterministic generation with message-driven titles, deep content, and visual variety for test environments.
6. **[NEW] `backend/app/content_qa/`** (`models.py`, `checker.py`, `repair.py`): Deterministic Content QA engine scoring title strength, depth, density, card ratios, and takeaway presence.
7. **[MODIFY] `backend/app/domain/presentation.py` & `enums.py`**: Backwards-compatible schema fields (`takeaway`, `key_message`, `objective`, `NarrativeStrategy`, `ContentDepth`).
8. **[MODIFY] `backend/app/visual_intelligence/selector.py`**: Deck-level rhythm enforcement to prevent repetitive card grids.
9. **[MODIFY] `backend/app/jobs/orchestrator.py`**: End-to-end orchestration of Multi-Stage Planning, Content QA, Refinement loop, Spatial QA, and Composite Quality Scoring.
10. **[MODIFY] `frontend/src/`**: Progress shells and diagnostic inspectors reflecting real backend stages and quality metrics.

### 11. Which modules should NOT be modified?
To prevent regression and maintain architectural integrity, the following modules **must NOT be rewritten**:
- `backend/app/rendering/engine.py`, `shapes.py`, `charts.py`, `tables.py`, `connectors.py`: Working native PPTX OpenXML rendering.
- `backend/app/reference/analyzer.py`, `color_extractor.py`, `font_extractor.py`: Working Phase 7 reference PPTX extraction.
- `backend/app/visual_qa/spatial.py`, `overflow.py`, `density.py`, `containment.py`: Working Phase 9 geometric QA checkers.
- `backend/app/artifacts/storage.py`: Working artifact lifecycle and TTL management.
- `backend/app/jobs/store.py`: Working in-memory job state store.
- Existing security controls in Phase 11/12 (rate limiting, file size limits, XML zip bomb protection, path traversal protection).

---

## Quality Upgrade Strategy Matrix

| Dimension | Current Weakness | Professional Target Architecture |
|---|---|---|
| **Storytelling** | Random collection of topical slides | Purpose-driven narrative arcs (Executive, Technical, Academic, Analytical) |
| **Slide Titles** | Generic nouns ("Overview", "Benefits", "Architecture") | Insight-driven action titles ("AI reduces decision latency by automating risk scoring") |
| **Content Depth** | 3–4 vague bullets with 2–4 words each | Substantive points (8–20 words) with mechanisms, tradeoffs, and evidence |
| **Visual Diversity** | High frequency of 3-card grids | Rhythmic variety: Hero -> Problem -> KPI -> Process -> Architecture -> Comparison -> Chart -> Roadmap |
| **Takeaways** | Absent; audience must infer the point | Explicit, prominent takeaway banner/callout on every core slide |
| **Data Integrity** | Unclear distinction between fact & illustration | Explicit provenance tracking; illustrative data clearly marked |
| **Quality Assurance** | Geometry & spatial QA only | Dual QA: Spatial Geometry QA + Deterministic Content QA with bounded repair |
| **Generation Speed vs Quality** | Fast single-shot generation | Deliberate multi-stage strategic planning (Quality > Speed) |
