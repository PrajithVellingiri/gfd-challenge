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
