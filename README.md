# AI Presentation Generator (PresenAI)

Production-grade web application platform that generates editable, professionally composed PowerPoint presentations from a topic prompt or by extracting and adapting the design language of a reference PowerPoint presentation.

---

## Architecture Overview

```text
[ Browser / React + TypeScript + Tailwind CSS (Vite) ]
                         │
                         ▼ (HTTP REST / SSE Correlation)
            [ FastAPI API Gateway ]
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
[ Request ID / Log ] [ Config / CORS ] [ Health Check ]
                         │
                         ▼
        [ AI Orchestration Layer (Phase 4) ]
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
[ GeminiProvider (google-genai) ]  [ FakeAIProvider (Offline / Testing) ]
       │
       ▼ (Native Structured JSON Schema)
[ Presentation Domain Schema (Phase 3) ]
       │
       ▼ (Future Phases)
[ Deterministic Layout Engine ──► Native PPTX Renderer ──► Visual QA ]
```

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
- **Backend**: Python 3.14+, FastAPI, Pydantic v2, Google GenAI SDK (`google-genai`), Starlette Middleware, Structured JSON Logging.

---

## Requirements

- **Python**: 3.14+ (or 3.12+)
- **Node.js**: v20+ (tested on v24.19.0)
- **npm**: v10+ (tested on v11.17.0)

---

## Getting Started

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# (Optional) Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend API will be accessible at: `http://127.0.0.1:8000`
Health Endpoint: `http://127.0.0.1:8000/health`
Interactive API Docs: `http://127.0.0.1:8000/docs`

#### Environment Configuration

Add the following to your backend `.env`:

```env
# AI Provider Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=60.0
AI_MAX_ATTEMPTS=2
```

> **Security Note**: `GEMINI_API_KEY` is strictly backend-only and is never committed or exposed to the frontend browser bundle.

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Run development server
npm run dev
```

Frontend will be accessible at: `http://localhost:5173`

---

## Testing & Quality Assurance

### Run Backend Tests

```bash
# From workspace root:
python -m pytest backend/tests -v
```

### Run Frontend Build & Type Check

```bash
# From frontend directory:
cd frontend
npm test
npm run build
```

---

## Current Status: Phase 8 — Semantic Visual Selection Intelligence Completed

### Implemented in Phases 1 through 8:

- [x] **FastAPI Application Factory & Architecture (Phase 1)**: CORS, correlation ID tracking (`X-Request-ID`), structured logging, `/health` endpoint.
- [x] **Landing Experience & Studio UI (Phase 2)**: Dual creation workflows (Mode A: Topic Creation, Mode B: Reference PPT Uploader), settings panel, progress & gallery shells, light/dark mode switcher.
- [x] **Presentation Domain Layer (Phase 3)**:
  - **Strict AI vs. Geometry Separation**: AI schemas describe semantics, narrative flow, visual archetypes, content blocks, charts, tables, and design tokens without raw physical coordinates or EMUs.
  - **Schema Versioning**: Canonical version `CURRENT_SCHEMA_VERSION = "1.0"` with strict integrity validation.
  - **Controlled Vocabularies (`enums.py`)**: `NarrativeRole` (14 roles), `VisualType` (25 archetypes), `ElementType` (15 types), `DataSource`, `TimelineStatus`, `TokenSource`, `Density`.
  - **Design System Models (`design_system.py`)**: `ColorToken` (hex validation + confidence scores), `Palette` (semantic roles), `TypographySystem`, `ShapeStyle`, `SpacingScale`, `LayoutPreferences`.
  - **Structured Data Models**: `ChartData` (matching series/categories + provenance tracking), `TableData` (matching row/column cells), `TimelineData`, `ProcessFlowData`.
  - **Root Presentation Schema (`presentation.py`)**: `Presentation`, `PresentationMetadata`, `Slide`, `Element` with duplicate ID prevention and sequential index validation.
  - **Job Lifecycle Schemas (`jobs.py`)**: `JobState`, `JobProgress`, `JobError`.
- [x] **AI Orchestration Layer (Phase 4)**:
  - **Provider Abstraction (`AIProvider`)**: Clean protocol interface decoupling the planning domain from specific AI SDKs.
  - **Production Gemini Provider (`GeminiProvider`)**: Official modern `google-genai` SDK integration utilizing native JSON structured output (`response_schema=Presentation`).
  - **Prompt Architecture (`PromptBuilder`)**: Modular prompt constructor with strict system instructions, narrative progression rules, anti-hallucination data integrity rules, and visual archetype guidance.
  - **Security & Injection Defense**: Untrusted user topics and reference PPT tokens are quarantined within `<user_topic>` and `<reference_untrusted_data>` delimiters with strict system override prohibitions.
  - **1-Pass Auto-Recovery (`OnePassRecoveryHandler`)**: Automatic error formatting and single-attempt repair prompt on schema mismatch, strictly capped at `MAX_AI_ATTEMPTS = 2`.
  - **Deterministic Fake AI Provider (`FakeAIProvider`)**: Full offline / test provider generating rich, validated `Presentation` blueprints with multi-slide visual diversity (`process_flow`, `timeline`, `kpi`, `card_grid`, `column_chart`, `table`).
- [x] **Native PPTX Rendering Engine (Phase 5)**:
  - Native OpenXML shape and typography rendering (`python-pptx`).
  - Native tables (`add_table`), native charts (`add_chart`), native connectors, and formatted speaker notes.
  - Zero full-slide rasterization; 100% editable OpenXML objects.
- [x] **Deterministic Layout Engine & 18 Layout Archetypes (Phase 6)**:
  - **Canonical 16:9 Canvas**: Abstract virtual coordinate space (1920 × 1080) with centralized EMU conversion (`EMU = round(virtual_unit * 6350)`).
  - **Mathematical Determinism**: Zero float drift, identical pixel coordinates on every repeated execution.
  - **18 Layout Archetypes**: Blank/Freeform, Title+Body, Hero, Two-Column, Three-Card Row, Four-Card Grid, KPI Dashboard, Split Comparison, Timeline, Process Flow, Flowchart, Hierarchy Tree, Architecture Diagram, 2x2 Matrix, Table + Summary, Chart + Insight, Quote, and Roadmap.
  - **Constraint & Boundary Validation**: Canvas containment checks, non-negative dimension assertions, child-in-parent boundary validation, and structured `LayoutWarning` items.
  - **Text Fitting & Metrics**: PIL font measurement with responsive container expansion (up to 15%) and minimum font threshold protection (14pt body, 11pt caption).
  - **Connector Port System**: Deterministic attachment ports on container borders (top, bottom, left, right, center).
- [x] **Reference PPT Intelligence Analyzer (Phase 7 — Mode B Foundation)**:
  - **Safe OpenXML Package Inspector (`SafePPTXPackage`)**: Safe ZIP bounds (max 500 files, max 50MB uncompressed), path traversal rejection, and pre-scan DTD/XXE entity defenses (`safe_parse_xml`).
  - **Color & Palette Extractor (`ColorExtractor`)**: Extracts theme color schemes (`clrScheme`), slide background fills (`<p:bg>`), full-bleed background shapes, text run fills, and synthesizes semantic `Palette` with ITU-R BT.709 luminance calculations and confidence scoring.
  - **Typography Extractor (`FontExtractor`)**: Extracts theme font schemes (`fontScheme`), slide run typefaces, heading vs body font frequency by size distribution, and synthesizes canonical `TypographySystem`.
  - **Shape & Geometry Extractor (`ShapeExtractor`)**: Analyzes preset geometries (`prstGeom`), corner radius preferences (12pt rounded vs 0pt crisp rectangular), stroke widths, and synthesizes `ShapeStyle`.
  - **Spacing & Density Extractor (`SpacingExtractor`)**: Analyzes shape density per slide, infers `Density` (`LOW`, `MEDIUM`, `HIGH`) and `WhitespacePreference`.
  - **Recurring Visual Motif Detector (`MotifDetector`)**: Heuristically detects tables, charts, process flows, timelines, card grids, KPI metrics, and comparison layouts.
  - **Sanitized AI Boundary**: ZERO slide body text, titles, speaker notes, proprietary text, or malicious prompt-injection payloads are ever leaked into the output `DesignSystem` or `DesignContext`.
- [x] **Semantic Visual Selection Intelligence (Phase 8)**:
  - **Content Semantic Classifier (`ContentSemanticClassifier`)**: Multi-signal detection across 10 categories (Temporal, Sequential, Hierarchical, Comparative, Quantitative, Relational, Tabular, Key Statement, Categorical, Prose).
  - **Deterministic Rule Engine (`VisualScoringEngine`)**: Multi-factor scoring balancing semantic match, narrative role match, data compatibility, reference motif bonuses, and deck visual budget repetition penalties.
  - **Canonical VisualType $\to$ Archetype Mapping (`ARCHETYPE_MAPPINGS`)**: Maps all 25 Phase 3 visual types to registered Phase 6 layout archetype resolvers with deterministic preferred and fallback options.
  - **Conservative Visual Data Builder (`VisualDataBuilder`)**: Safely synthesizes `TimelineData`, `ProcessFlowData`, `TableData`, and `ChartData` with data validation and anti-hallucination labeling (`DataProvenance.ILLUSTRATIVE`).
  - **Deck-Level Visual Budget (`DeckVisualBudget`)**: Enforces slide-level visual diversity, caps consecutive identical card layouts, and balances deck narrative progression.
  - **End-to-End Integration**: Seamlessly bridges Phase 4 AI planning with Phase 6 LayoutEngine and Phase 5 PPTX Renderer with 100% deterministic test coverage.
- [x] **Automated Test Suite**: **144 backend tests** (`pytest`) covering visual intelligence classification, scoring, negative cases, data validation, reference motif weighting, determinism, layout archetypes, canvas conversion, geometry constraints, AI prompts, fake provider, and domain schemas + **10 frontend UI unit tests** (`vitest`).
- [x] **Production Build Verification**: Full TypeScript compilation and asset bundling verified with zero errors.

---

## Roadmap & Next Phase

- **Next Up: Phase 9 — Visual QA & 3-Pass Auto-Correction Engine**
- Phase 10: Asynchronous Job Pipeline & Download Delivery
- Phase 11: Real-Time SSE Streaming & Visual Canvas Diagnostics
- Phase 12: Production Hardening, Rate Limiting & Cloud Packaging

#   P p t - c r e a t o r -  
 