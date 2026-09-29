# Phase 1: Database + Storage Foundation

## 1. Architecture Overview
Phase 1 establishes the cloud database and object storage foundation for the GFD Challenge DPI (Digital Public Infrastructure) system using **Supabase** (PostgreSQL 15+ with PostGIS) and **FastAPI**.

```
[ Citizen / Client ] ────────► [ FastAPI Gateway ] ────────► [ Supabase PostgreSQL (PostGIS) ]
        │                             │                                   ▲
        │ (Direct upload with RLS)    │ (Storage URL validation)          │ (Spatial Queries)
        ▼                             ▼                                   │
[ Supabase Storage ] ◄────────────────┴───────────────────────────────────┘
  ├── citizen-images (Private)
  └── citizen-audio  (Private)
```

---

## 2. Supabase Setup & Extensions

### Required Extensions
1. `uuid-ossp`: For generating unique UUID identifiers (`gen_random_uuid()`).
2. `postgis`: Enables geospatial features, `GEOGRAPHY(Point, 4326)`, and `GEOMETRY(MultiPolygon, 4326)` for districts, facilities, and citizen request locations.

### Storage Buckets
1. **`citizen-images`**:
   - Visibility: **Private** (`public = false`)
   - Max file size: 10 MB
   - Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/jpg`
   - Path structure: `{user_id}/{request_id}/{filename}`
2. **`citizen-audio`**:
   - Visibility: **Private** (`public = false`)
   - Max file size: 25 MB
   - Allowed MIME types: `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`, `audio/webm`, `audio/x-m4a`
   - Path structure: `{user_id}/{request_id}/{filename}`

---

## 3. Database Schema Summary

| Table | Purpose | Primary Keys & References | PostGIS / Spatial Elements |
|---|---|---|---|
| `users` | User profiles synced with Supabase Auth | `id UUID PRIMARY KEY REFERENCES auth.users(id)` | N/A |
| `districts` | Administrative boundaries (supports BRICS) | `id UUID PRIMARY KEY`, `UNIQUE(name, state, country)` | `boundary GEOMETRY(MultiPolygon, 4326)`, `centroid GEOMETRY(Point, 4326)` |
| `citizen_requests` | Core citizen reports & grievances | `id UUID PRIMARY KEY`, `user_id -> users(id)` | `location GEOGRAPHY(Point, 4326)` auto-synced via trigger from `(lat, lon)` |
| `infrastructure` | Generic public infrastructure assets | `id UUID PRIMARY KEY`, `district_id -> districts(id)` | `location GEOGRAPHY(Point, 4326)` auto-synced via trigger |
| `demographics` | Extensible census and demographic data | `id UUID PRIMARY KEY`, `district_id -> districts(id)` | Flexible `demographic_indicators JSONB` |
| `investments` | Public capital & budget allocations | `id UUID PRIMARY KEY`, `district_id -> districts(id)` | Amount, currency (`INR`, `BRL`, etc.), financial year |
| `ai_analyses` | Flexible AI inference outputs (Phase 2+) | `id UUID PRIMARY KEY`, `request_id -> citizen_requests(id)` | `analysis_json JSONB`, `entities JSONB`, confidence |

---

## 4. Row Level Security (RLS) & Policies

RLS is strictly enforced on all tables and storage objects:
- **`citizen_requests`**:
  - Citizens can **INSERT** and **SELECT** only their own requests (`user_id = auth.uid()`).
  - Citizens can edit/cancel requests only while in `submitted` status.
  - Policymakers and Admins have broad read access across all requests.
- **Reference Tables (`districts`, `infrastructure`, `demographics`, `investments`)**:
  - Read access is available to authenticated and anonymous users for transparent public data.
  - Write access (INSERT, UPDATE, DELETE) is restricted strictly to Admins.
- **`storage.objects`**:
  - Uploads and downloads are restricted to authenticated users matching folder prefix `(storage.foldername(name))[1] = auth.uid()::text`.
  - Policymakers and Admins can view citizen media attachments.
  - Public anonymous downloads are rejected.

---

## 5. Migration Execution

Migrations are idempotent and reproducible across any PostgreSQL/Supabase database:

```bash
# Set your DATABASE_URL in .env
python backend/apply_migrations.py
```
Or execute the SQL scripts sequentially via the Supabase SQL editor:
1. `backend/migrations/001_initial_schema.sql`
2. `backend/migrations/002_storage_setup.sql`
3. `backend/migrations/003_rls_policies.sql`
