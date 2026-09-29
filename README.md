# GFD Challenge

A Digital Public Infrastructure (DPI) & Governance platform for citizen grievances, spatial infrastructure tracking, and governance analytics.

## Project Structure

```
GFD challenge/
├── frontend/       # User interface and client-side applications
├── backend/        # Server-side logic, APIs, and business services
├── ml/             # Machine learning models, training, and evaluation scripts
├── data/           # Datasets, raw inputs, and processed artifacts
├── docs/           # Documentation, architectural designs, and notes
└── README.md       # Project overview and documentation
```

---

## Phase 1 — Database & Storage

### Architecture
Phase 1 establishes the cloud database, spatial engine, and object storage foundation using **Supabase** (PostgreSQL 15+ with PostGIS) and a lightweight **FastAPI** backend:

- **Relational Data**: Managed in Supabase PostgreSQL with UUID primary keys and relational integrity.
- **Geographic Engine**: PostGIS enabled for boundary multipolygons, centroids, and request coordinates with GIST spatial indexes.
- **Object Storage**: Private Supabase Storage buckets for citizen image and audio uploads, storing only relative path references in PostgreSQL.
- **Backend API**: FastAPI service exposing health check, secure request validation, and upload path generation.

### Environment Variables
Environment templates are provided. Never commit live `.env` files.

- **Backend** (`backend/.env.example`):
  - `SUPABASE_URL`: Supabase project URL (`https://<project-id>.supabase.co`)
  - `SUPABASE_KEY`: Supabase public anon key
  - `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role secret key
  - `DATABASE_URL`: Direct PostgreSQL connection string with SSL
  - `CORS_ORIGINS`: Comma-separated list of allowed origins
  - `ENVIRONMENT`: `development` | `production` | `test`
  - `STORAGE_IMAGE_BUCKET`: `citizen-images`
  - `STORAGE_AUDIO_BUCKET`: `citizen-audio`
- **Frontend** (`frontend/.env.example`):
  - `VITE_SUPABASE_URL`: Supabase project URL
  - `VITE_SUPABASE_ANON_KEY`: Supabase public anon key
  - `VITE_API_BASE_URL`: Backend API URL (e.g., `http://localhost:8000`)

### Supabase Setup
1. Create a Supabase project.
2. Enable required extensions in PostgreSQL:
   - `uuid-ossp`
   - `postgis`

### Database Schema
Core tables provisioned in `backend/migrations/001_initial_schema.sql`:
- **`users`**: Profiles synchronized with Supabase Auth (`id`, `name`, `email`, `role`, timestamps). Roles: `citizen`, `policymaker`, `admin`.
- **`districts`**: Administrative boundaries supporting BRICS nations (`id`, `name`, `state`, `country`, `boundary`, `centroid`, timestamps).
- **`citizen_requests`**: Core requests and grievances (`id`, `user_id`, `description`, `category`, `language`, `latitude`, `longitude`, `location`, `location_name`, `urgency`, `status`, `image_path`, `audio_path`, future AI fields, timestamps).
- **`infrastructure`**: Generic public facilities across healthcare, education, water, roads, electricity, and digital infrastructure (`id`, `district_id`, `category`, `name`, `latitude`, `longitude`, `location`, `capacity_value`, `source`, timestamps).
- **`demographics`**: Population metrics and indicators extensible for Census/NFHS data (`id`, `district_id`, `population`, `rural_population`, `urban_population`, `demographic_indicators`, `year`, `source`).
- **`investments`**: Capital investments and financial allocations (`id`, `district_id`, `category`, `amount`, `currency`, `financial_year`, `source`, timestamps).
- **`ai_analyses`**: Separate entity for AI inferences (`id`, `request_id`, `detected_language`, `translated_text`, `extracted_category`, `extracted_location`, `extracted_urgency`, `entities`, `confidence`, `model_name`, `analysis_json`).

### Storage Buckets
Configured in `backend/migrations/002_storage_setup.sql`:
- **`citizen-images`**: Private (`public = false`), 10 MB limit, types: JPEG, PNG, WebP.
- **`citizen-audio`**: Private (`public = false`), 25 MB limit, types: MP3, WAV, OGG, M4A, WebM.
- **Path convention**: `{user_id}/{request_id}/{filename}` to isolate citizen files and prevent arbitrary filename exposure.

### RLS / Security
Configured in `backend/migrations/003_rls_policies.sql`:
- Row Level Security (RLS) enabled on all 7 core tables.
- **Citizens**: Allowed to create and read only their own requests (`user_id = auth.uid()`). No permission to modify reference datasets or view other citizens' private submissions.
- **Policymakers / Admins**: Broad read access for governance analysis; administrative write access for public datasets.
- **Storage Objects**: Access restricted by folder prefix to authenticated file owners; unauthorized access is blocked.
- **Credential Protection**: No secrets hardcoded in codebase; `.env` excluded from version control via `.gitignore`.

### Migration Instructions
Migrations are sequential and idempotent:
```bash
# Apply via Python runner using DATABASE_URL:
python backend/apply_migrations.py

# Or run files in order via Supabase SQL Editor:
# 1. backend/migrations/001_initial_schema.sql
# 2. backend/migrations/002_storage_setup.sql
# 3. backend/migrations/003_rls_policies.sql
```

### Local Development
```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run test suite
pytest tests -v

# 4. Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Health endpoint is accessible at `http://localhost:8000/health` and OpenAPI docs at `http://localhost:8000/docs`.

---

## Phase 2 — Dataset Pipeline

### Ingestion & Processing Architecture
Phase 2 establishes the end-to-end data pipeline in `data/`, normalizing public official datasets, spatial boundaries, and realistic synthetic demand data into canonical models:

- **Canonical District Normalization**: Resolves spelling variations, legacy names, and aliases (e.g. Bangalore -> Bengaluru Urban, Poona -> Pune) to canonical district records with deterministic UUID5 identifiers.
- **Geographic Validation (PostGIS / EPSG:4326)**: District polygons and centroids validated using Shapely; spatial bounds strictly enforced.
- **Data Provenance & Registry**: Sourced datasets categorized into `official`, `public`, or `synthetic` in [`data/DATA_SOURCES.md`](file:///d:/College/Projects/GFD%20Challenge/data/DATA_SOURCES.md).

### Datasets Summary

| Dataset | Source | Records | Data Type | Target Table |
|---|---|---|---|---|
| **Districts GIS** | Survey of India / DataMeet | 44 districts | `public` | `districts` |
| **Demographics** | Census of India 2011 (ORGI) | 44 records | `official` | `demographics` |
| **Healthcare Infrastructure** | HMIS / MoHFW | 56 facilities | `official` | `infrastructure` |
| **Health Indicators** | NFHS-5 Factsheets (IIPS / MoHFW) | 308 indicators | `official` | `health_indicators` |
| **Investments** | Synthetic Simulation Model | 660 records | `synthetic` | `investments` |
| **Citizen Demand Requests** | Synthetic Hotspot Engine | 8,000 requests | `synthetic` | `citizen_requests` |

### Running the Dataset Pipeline
```bash
# 1. Regenerate all normalized datasets
python data/scripts/prepare_districts_gis.py
python data/scripts/prepare_demographics.py
python data/scripts/prepare_infrastructure.py
python data/scripts/prepare_health_indicators.py
python data/scripts/prepare_investments.py
python data/scripts/generate_citizen_requests.py

# 2. Run data quality validation & profiling
python data/scripts/profile_datasets.py

# 3. Test ingestion dry-run
python data/scripts/load_all_to_database.py --dry-run

# 4. Ingest into live Supabase / PostgreSQL (requires DATABASE_URL in .env)
python data/scripts/load_all_to_database.py
```

---

## Phase 3 — Citizen Submission System

### Citizen Submission Workflow
Phase 3 implements the citizen-facing grievance submission workflow:
```
Citizen ──► Login/Demo ──► Request Form (Text + Image <10MB + Voice <25MB + Location)
           ──► Validation ──► FastAPI (/api/requests) ──► PostGIS District Containment
           ──► Supabase PostgreSQL + Storage ──► Confirmation ──► Request History
```

- **Frontend Citizen Portal**: React 18 + Vite responsive portal with GPS geolocation, manual district selection, image upload with preview, in-browser `MediaRecorder` voice notes, and submission confirmation.
- **Request History**: Citizens can view their past submissions, urgency status, and attached media indicators (📷 Photo, 🎤 Voice) in a dedicated dashboard.
- **District Auto-Association**: Point-in-polygon containment resolution automatically maps coordinates to canonical district UUIDs.
- **Security & RLS**: Strict path isolation (`{user_id}/{request_id}/{filename}`) and ownership checks ensure private grievances cannot be accessed or tampered with by other users.

### Running Phase 3 Tests
```bash
# Run backend pytest suite (Phase 1, 2, and 3 tests)
python -m pytest -v

# Run frontend component & validation tests
cd frontend && npm test
```

---

## Phase 4 — Multimodal AI Intelligence

### Multimodal Analysis Workflow
Phase 4 integrates Google's Gemini models (`gemini-1.5-flash`) to transform raw citizen requests (text, voice audio, field photos) into structured, actionable governance intelligence:

```
Citizen Submission (Text, Voice WebM, Photo JPEG/PNG)
                     │
                     ▼
          [Backend Request Analyzer]
     (app/services/ai/request_analyzer.py)
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
Text Analysis  Audio Analyzer  Image Analyzer
(Gemini Flash)  (Gemini Audio) (Gemini Vision)
     │               │               │
     └───────────────┼───────────────┘
                     ▼
         Output Validation & Clean
        (app/services/ai/validators.py)
                     │
                     ▼
        PostgreSQL / Supabase Storage
        - public.ai_analyses (v1.0 schema)
        - processing_status: completed / failed
                     │
                     ▼
         Frontend AI Insight Drawer
        (src/components/AIAnalysisCard.jsx)
```

- **Multilingual Understanding**: Translates Tamil, Hindi, and regional language complaints to clear English while preserving all specific nuances and local names.
- **Canonical Categorization**: Strictly classifies grievances into 8 official DPI sectors (`Healthcare`, `Education`, `Roads`, `Water`, `Transportation`, `Electricity`, `Digital Infrastructure`, `Other`).
- **Urgency & Sub-Category Assessment**: Categorizes urgency as `Low`, `Medium`, `High`, or `Critical`, and extracts specific sub-categories.
- **Audio Transcription**: Automatically transcribes citizen voice recordings into faithful text.
- **Computer Vision Inspection**: Identifies infrastructure types and extracts 1–5 objective visual observations with physical severity estimation.
- **Summarization & Keywords**: Produces concise summaries (<=200 chars) and 3–10 keywords.
- **Interactive UI Insights**: Integrates `AIAnalysisCard` directly in request history and post-submission screens with clear advisory notices.

### Running Test Suites
```bash
# Backend test suite (Phase 1, 2, 3, and 4 — 60 tests)
$env:PYTHONPATH=".;backend"; python -m pytest -v

# Frontend component tests & production Vite build
cd frontend
npm test
npm run build
```

---

## Phase 5 — Request Intelligence

### Relational Intelligence Architecture
Phase 5 transforms individual analyzed citizen requests into relational community intelligence:

```
Individual Citizen Requests
            ↓
Semantic Vector Embeddings (768-dim)
            ↓
Pairwise Cosine Similarity & Nearest Neighbors
            ↓
Duplicate / Near-Duplicate Detection (Geographically Verified)
            ↓
District-Aware Semantic Clustering (DBSCAN)
            ↓
Emerging Issue & Surge Detection (Period-over-Period Growth)
```

- **Semantic Vector Embeddings**: 768-dimensional normalized embeddings with provider abstraction (Google Gemini `models/text-embedding-004` and deterministic mock fallback).
- **Duplicate vs. Similar Differentiation**: Enforces location awareness—high semantic similarity across different districts is classified as *similar*, while identical needs in the same locality are flagged as *duplicates*.
- **District-Aware Semantic Clustering**: Employs DBSCAN with precomputed cosine distance matrices partitioned by `(district_id, category)`, synthesizing deterministic human-readable cluster labels from member sub-categories and keywords.
- **Emerging Issue Surge Detection**: Compares request volume in current observation windows against prior windows, transparently calculating period-over-period growth and reporting `AI/data-derived signals`.
- **Privacy-Guaranteed Citizen UI**: Anonymized similarity counts and duplicate groups rendered in `RequestIntelligenceSection.jsx` without leaking personal identities.

### Running Complete Test Suite
```bash
# Backend test suite (Phase 1, 2, 3, 4, 5, and 6 — 101 tests)
$env:PYTHONPATH=".;backend"; python -m pytest -v

# Frontend component tests & production Vite build
cd frontend
npm test
npm run build
```

---

## Phase 6 — Infrastructure Intelligence & Gap Detection

### Architecture & Gap Detection Engine
Phase 6 connects citizen demand intelligence (Phase 3–5) with public infrastructure availability and demographic datasets (Phase 1–2):

```
       Citizen Demand (Phase 3-5)          Public Infrastructure & Demographics (Phase 1-2)
  (Total requests, 7d growth, per 10k)       (Census 2011, HMIS facilities, NFHS-5, Investments)
                   \                                        /
                    \                                      /
                     ▼                                    ▼
                 Relative Cross-District Percentile Ranking (0 - 100%)
                                          ↓
               Explainable Decision-Support Indicators & Gap Signals
               - potential_gap (High Demand + Low Infrastructure)
               - infrastructure_pressure (High Demand + Moderate Infrastructure)
               - demand_supply_signal (Concentrated Grievance Clusters)
               - balanced (Demand and Infrastructure in Alignment)
               - insufficient_data (Sample size or public records missing)
```

- **Population Normalization**: Per-capita rates safely computed (facilities/100k, beds/10k, doctors/10k, requests/10k) with zero-divisor guards.
- **Relative Cross-District Percentiles**: Standardized comparative rankings (0th to 100th percentile) across all 44 canonical districts.
- **Transparent Data Provenance**: Every record explicitly distinguishes official datasets (Census 2011, HMIS, NFHS-5) from synthetic hackathon engines with timestamps, citations, and limitation notes.
- **Explainable Decision-Support Signals**: Rule-based mismatch indicators with structured observations (`what_was_observed`, `infrastructure_observed`, `why_signal_generated`) avoiding opaque composite scores.
- **Privacy & PII Isolation**: Aggregated district-level metrics ensure zero citizen personal identifier leakage.
- **Reusable Frontend Components**: Modular UI elements (`DemandMetricCard`, `InfrastructureMetricCard`, `GapSignalCard`, `DataProvenance`, `DistrictIntelligenceCard`).

### Verification & Testing
```bash
# Run all Phase 1-6 backend automated tests (101 tests)
$env:PYTHONPATH=".;backend"; python -m pytest -v

# Run frontend tests & production Vite build
cd frontend
npm test
npm run build
```





