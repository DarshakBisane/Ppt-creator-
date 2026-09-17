# AI Presentation Generator (PresenAI)

Production-grade web application platform that generates editable, professionally composed PowerPoint presentations from a topic prompt or by extracting and adapting the design language of a reference PowerPoint presentation.

---

## 1. System Architecture

```text
                                 ┌─────────────────────────────────────────┐
                                 │     Browser / React 19 + TypeScript     │
                                 │  Tailwind CSS v4 • Lucide • Vite Build  │
                                 └────────────────────┬────────────────────┘
                                                      │ (HTTP / JSON / Multipart)
                                                      ▼
                                 ┌─────────────────────────────────────────┐
                                 │       FastAPI Gateway & Middleware      │
                                 │  RequestId • Strict CORS • JSON Logger  │
                                 └────────────────────┬────────────────────┘
                                                      │
                         ┌────────────────────────────┼────────────────────────────┐
                         ▼                            ▼                            ▼
                 [ Health Check ]           [ MemoryJobStore ]             [ ArtifactStorage ]
                 GET /health (Fast)       (Process-Local 1-Worker)         (Sandboxed OpenXML)
                         │                            │                            │
                         │                            ▼                            │
                         │             [ Generation Orchestrator ]                 │
                         │                            │                            │
                         │            ┌───────────────┴───────────────┐            │
                         │            ▼                               ▼            │
                         │   [ Mode A: Topic ]              [ Mode B: Reference ]  │
                         │            │                     (Safe Package Parser)  │
                         │            ▼                               │            │
                         │   [ Gemini AI Orchestration ] ◄────────────┘            │
                         │   (google-genai / Structured JSON)                      │
                         │            │                                            │
                         │            ▼                                            │
                         │   [ Semantic Visual Selector ]                          │
                         │   (25 Archetypes • Deck Budget • Motif Weights)         │
                         │            │                                            │
                         │            ▼                                            │
                         │   [ Deterministic Layout Engine ]                       │
                         │   (1920x1080 Canonical Space • EMU Conversion)          │
                         │            │                                            │
                         │            ▼                                            │
                         │   [ Visual QA & Repair Engine ]                         │
                         │   (3-Pass Monotonic Correction • Bounds & Overlap)      │
                         │            │                                            │
                         │            ▼                                            │
                         │   [ Native OpenXML PPTX Renderer ]                      │
                         │   (python-pptx • 100% Native Shapes/Charts/Tables)      │
                         │            │                                            │
                         └────────────┼────────────────────────────────────────────┘
                                      ▼
                        [ Downloadable Native .pptx ]
```

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, Vitest, Nginx SPA container.
- **Backend**: Python 3.14 / 3.12, FastAPI, Uvicorn, Pydantic v2, `google-genai` SDK, `python-pptx`, Pillow, Pytest.
- **AI Planning**: Google Gemini (`gemini-2.5-flash`) with native structured JSON schema enforcement and offline `FakeAIProvider`.
- **Presentation Output**: 100% native OpenXML presentation objects (shapes, connectors, tables, native charts, typography). Zero full-slide rasterization.

---

## 2. Environment Variables Reference

| Variable | Required | Default | Purpose | Example / Format |
| :--- | :---: | :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Yes** (Prod) | *None* | Google Gemini AI Studio API key | `AQ.Ab8RN6...` |
| `ENVIRONMENT` | No | `development` | Runtime environment (`development`, `test`, `production`) | `production` |
| `APP_NAME` | No | `"AI Presentation Generator"` | Application display name | `"PresenAI"` |
| `API_HOST` | No | `127.0.0.1` | Network interface for FastAPI to bind | `0.0.0.0` |
| `API_PORT` | No | `8000` | Port for FastAPI server | `8000` |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `CORS_ORIGINS` | No | `http://localhost:5173,...` | Allowed CORS origins (comma-separated or JSON list) | `http://localhost:3000,https://app.example.com` |
| `ENABLE_DOCS` | No | `false` in prod | Enable `/docs` and `/redoc` in production | `false` |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model variant | `gemini-2.5-flash` |
| `AI_TIMEOUT_SECONDS` | No | `60.0` | Timeout threshold for AI planning calls | `60.0` |
| `AI_MAX_ATTEMPTS` | No | `2` | 1-pass auto-recovery retry budget | `2` |
| `ARTIFACT_DIR` | No | `temp/artifacts` | Sandboxed storage directory for generated PPTX files | `/app/temp/artifacts` |
| `ARTIFACT_TTL_SECONDS`| No | `3600` | Expiration time for temporary artifacts in seconds | `3600` |
| `MAX_CONCURRENT_JOBS` | No | `5` | Semaphore bounding concurrent generation jobs | `5` |
| `MAX_JOB_RUNTIME_SECONDS` | No | `300` | Stuck-job watchdog timeout limit in seconds | `300` |
| `VITE_API_BASE_URL` | No (Frontend)| `""` (relative) | Backend API endpoint used by the React web app | `http://localhost:8000` |

> [!WARNING]
> **Security Guardrail**: `GEMINI_API_KEY` is strictly backend-only. Never expose private credentials in `frontend/.env` or build arguments. Only `VITE_*` prefixed variables are bundled into client-side assets.

---

## 3. Local Development Setup

### Prerequisites
- **Python**: 3.14+ (or 3.12+)
- **Node.js**: v20+
- **npm**: v10+

### Step 1: Clone Repository
```bash
git clone https://github.com/DarshakBisane/Ppt-creator-.git
cd Ppt-creator-
```

### Step 2: Backend Setup & Execution
```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure backend environment
cp backend/.env.example backend/.env
# (Edit backend/.env and set your GEMINI_API_KEY)

# 4. Start FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Backend API: `http://127.0.0.1:8000`
- Health Check: `http://127.0.0.1:8000/health`
- Swagger Docs (Dev Mode): `http://127.0.0.1:8000/docs`

### Step 3: Frontend Setup & Execution
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure frontend environment
cp .env.example .env

# 3. Start development server
npm run dev
```

- Frontend Studio: `http://localhost:5173`

---

## 4. Docker Containerization & Orchestration

### A. Docker Compose (Full Stack)
To run both frontend and backend in production-configured Docker containers:

```bash
# 1. Configure environment variables in root .env
cp .env.example .env
# Edit .env to set GEMINI_API_KEY

# 2. Build and run containers
docker compose up --build -d

# 3. Verify container status and health
docker compose ps
docker compose logs -f
```

- Frontend App: `http://localhost:3000`
- Backend Health: `http://localhost:8000/health`

### B. Building Backend Container Manually
```bash
docker build -t presenai-backend:latest -f backend/Dockerfile backend/

docker run -d \
  --name presenai-backend \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_gemini_api_key_here" \
  -e ENVIRONMENT="production" \
  presenai-backend:latest
```

### C. Building Frontend Container Manually
```bash
docker build \
  --build-arg VITE_API_BASE_URL="http://localhost:8000" \
  -t presenai-frontend:latest \
  -f frontend/Dockerfile frontend/

docker run -d \
  --name presenai-frontend \
  -p 3000:80 \
  presenai-frontend:latest
```

---

## 5. Production Deployment Architecture

### Frontend (Static SPA Hosting)
- Build static production assets:
  ```bash
  cd frontend
  npm run build
  ```
- Output directory: `frontend/dist`
- Deploy to any static file hosting service (Nginx, AWS S3 + CloudFront, Vercel, Cloudflare Pages).
- Ensure SPA fallback routing is configured (`try_files $uri $uri/ /index.html;` or redirect all non-file routes to `/index.html`).

### Backend (FastAPI Service)
- Production startup command:
  ```bash
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
  ```
- Healthcheck Endpoint: `GET /health`

---

## 6. Architecture & Scaling Constraints

> [!IMPORTANT]
> **Single-Worker Process-Local Architecture**:
> The application uses an in-memory thread-safe `MemoryJobStore` for tracking presentation generation lifecycle states (`QUEUED` $\to$ `PLANNING` $\to$ `DESIGNING` $\to$ `QA` $\to$ `RENDERING` $\to$ `COMPLETED`).
> 
> Therefore:
> - The production backend **must run as a single process/worker (`--workers 1`)**.
> - Configuring multiple uvicorn worker processes will partition in-memory job state across OS process boundaries, leading to 404s during job status polling.
> - Horizontal scaling across multiple worker instances requires a shared persistent job store (e.g. distributed store/Redis) and is explicitly out of scope for Phase 12.

---

## 7. Artifact Storage & Lifecycle Management

- **Storage Sandboxing**: All generated presentations are saved in isolated directories under `temp/artifacts/{job_id}/{sanitized_filename}.pptx`.
- **Path Traversal Defense**: Strict filename and job ID sanitization defangs `..`, `/`, `\`, and absolute drive paths.
- **OpenXML Verification**: Every generated payload is validated as a legitimate OpenXML zip package before writing to disk and before download.
- **Ephemeral Storage**: In containerized environments, generated artifacts reside in the `/app/temp/artifacts` directory (or named docker volume `artifacts_data`).
- **TTL Cleanup**: Artifacts older than `ARTIFACT_TTL_SECONDS` (default: 1 hour) are automatically purged. Container restarts will discard ephemeral artifacts unless an external volume is mounted.

---

## 8. Testing & Validation

### Run Complete Backend Test Suite
```bash
python -m pytest backend/tests -v
```
*Current test suite: **266 tests**, 100% pass rate covering API endpoints, AI prompts, FakeAIProvider, LayoutEngine, Visual QA, Reference PPT Analyzer, Hardening limits, and Deployment configurations.*

### Run Frontend Unit Tests
```bash
cd frontend
npm test
```
*Vitest suite: **10 tests**, 100% pass rate covering Studio UI, Mode A / Mode B switches, input validation, and pipeline transitions.*

### Run Live Mode A & Mode B Smoke Tests
```bash
python scratch/run_live_smoke_tests.py
```
*Validates real Gemini API generation, OpenXML package integrity, slide counts, and native editable shapes.*

---

## 9. Troubleshooting Guide

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| `API returns 500: AI generation failed` | Missing or invalid `GEMINI_API_KEY` | Ensure `GEMINI_API_KEY` is set in `.env` or container environment. Test with `FakeAIProvider` by setting `ENVIRONMENT=test`. |
| `CORS error in browser console` | Origin not whitelisted | Add your frontend URL (e.g. `http://localhost:3000`) to `CORS_ORIGINS` in `.env`. |
| `404 Not Found on /api/jobs/{id}` | Multiple workers or expired TTL | Ensure backend runs with `--workers 1`. Verify `ARTIFACT_TTL_SECONDS`. |
| `Cannot connect to Docker daemon` | Docker Desktop daemon is not running | Start the Docker Desktop application / system service, or execute using direct local Python/Node commands. |
| `Swagger /docs returns 404` | Docs disabled in production | Set `ENABLE_DOCS=true` in `.env` if API documentation is needed in production. |

---

## 10. Implementation Status Summary

- [x] **Phase 1**: FastAPI Application Factory, Request ID Middleware, Structured Logging, Health Check.
- [x] **Phase 2**: Landing Page & Presentation Studio UI (Mode A Topic + Mode B Reference PPT).
- [x] **Phase 3**: Presentation Domain Layer, Strict AI/Geometry Separation, Schemas & Enums.
- [x] **Phase 4**: AI Orchestration Layer (`GeminiProvider`, `PromptBuilder`, 1-Pass Auto-Recovery, `FakeAIProvider`).
- [x] **Phase 5**: Native OpenXML PPTX Rendering Engine (`python-pptx`, native shapes, tables, charts, zero rasterization).
- [x] **Phase 6**: Deterministic Layout Engine & 18 Layout Archetypes (1920x1080 canonical space, EMU conversion).
- [x] **Phase 7**: Reference PPT Intelligence Analyzer (Safe package extractor, palette, typography, shape style extractor).
- [x] **Phase 8**: Semantic Visual Selection Intelligence (10 semantic categories, rule engine, visual budget).
- [x] **Phase 9**: Visual QA & 3-Pass Auto-Correction Engine (Boundary, text overflow, overlap, and monotonicity guarantees).
- [x] **Phase 10**: Asynchronous Job Pipeline & Download Delivery (`MemoryJobStore`, `ArtifactStorage`, FileResponse).
- [x] **Phase 11**: Production Hardening, Rate Limiting, Request Bounds, XML entity defense & Security Defenses.
- [x] **Phase 12**: Deployment & Containerization (Dockerfiles, Docker Compose, Nginx SPA, Environment standard, Full tests).