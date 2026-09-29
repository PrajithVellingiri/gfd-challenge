# GFD Challenge — Production Deployment Guide

This guide provides end-to-end instructions for deploying the **GFD Challenge Digital Public Infrastructure (DPI) & Governance Platform** to production using **Supabase** (Database, Auth, Storage), **Render / Railway** (FastAPI Backend), and **Vercel** (React/Vite Frontend).

---

## 1. Architecture Overview

```
                                  [ Citizen / Policymaker Browser ]
                                                  │
                                                  ▼
                               [ Frontend: Vercel (React + Vite SPA) ]
                                     │                      │
                      (Client Auth & Storage SDK)      (API Calls via HTTPS)
                                     │                      │
                                     ▼                      ▼
                       [ Supabase Cloud Platform ] ◄── [ Backend: Render / Railway ]
                       ├── PostgreSQL 15 + PostGIS       ├── FastAPI Service
                       ├── pgvector (768-dim)            ├── Gemini 1.5 Flash
                       ├── Supabase Auth (JWT/RLS)       └── DPI Intelligence Engines
                       └── Private Storage Buckets
```

---

## 2. Supabase Cloud Setup

### 2.1 Project Initialization
1. Log in to [Supabase Console](https://supabase.com).
2. Create a new organization and project (e.g. `gfd-challenge-prod`).
3. Select an AWS region close to the target audience (e.g., `ap-south-1` Mumbai).
4. Record your **Project URL**, **Anon Public Key**, and **Service Role Secret Key** from `Project Settings > API`.
5. Under `Project Settings > Database`, copy the direct PostgreSQL connection string (URI with `sslmode=require`).

### 2.2 Enabling Required Extensions
Open the **Supabase SQL Editor** and execute:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";
```

### 2.3 Applying Database Migrations
Migrations are strictly sequential and idempotent. Run the 7 migrations in order via the Supabase SQL Editor or using the automated Python migration runner:

```bash
# Set your DATABASE_URL in your deployment terminal
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require"
python backend/apply_migrations.py
```

The migrations establish:
- `001_initial_schema.sql`: Core users, districts (PostGIS polygons), citizen_requests, infrastructure, demographics, investments, and ai_analyses.
- `002_storage_setup.sql`: Supabase Storage bucket registration (`citizen-images`, `citizen-audio`) and owner-isolation policies.
- `003_rls_policies.sql`: Row Level Security policies guaranteeing citizen isolation and role segregation.
- `004_health_indicators.sql`: Health indicators and NFHS-5 factsheet indicators table.
- `005_ai_analyses_enhancements.sql`: Multimodal vision, audio transcription, urgency, and 768-dim embedding column.
- `006_request_intelligence.sql`: pgvector extension, HNSW cosine index, request embeddings, similarity graphs, DBSCAN clusters, and emerging issues.
- `007_infrastructure_intelligence.sql`: District intelligence metrics, relative benchmarks, and explainable gap signal registries.

---

## 3. Supabase Storage Configuration

Verify the storage buckets under `Storage > Buckets` in Supabase:
1. **`citizen-images`**:
   - Visibility: **Private** (`public = false`)
   - Max file size: **10 MB**
   - Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`
2. **`citizen-audio`**:
   - Visibility: **Private** (`public = false`)
   - Max file size: **25 MB**
   - Allowed MIME types: `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/webm`, `audio/mp4`, `audio/x-m4a`

**Storage Path Format**:
`{user_id}/{request_id}/{filename}`  
Row-level storage policies restrict reads and uploads to the file owner (`auth.uid()`).

---

## 4. Backend Deployment (Render / Railway)

### 4.1 Deployment on Render
1. Connect your GitHub repository to [Render](https://render.com).
2. Choose **Web Service**.
3. Configure settings:
   - **Name**: `gfd-challenge-backend`
   - **Environment**: `Python 3`
   - **Region**: Singapore or Frankfurt (choose nearest to database)
   - **Root Directory**: `backend` (or leave root and use root Procfile)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Configure **Environment Variables** (see Section 5 below).
5. Set Health Check Path to: `/health`

### 4.2 Deployment on Railway
1. Create a **New Project** from GitHub repo in [Railway](https://railway.app).
2. Set Root Directory to `/backend`.
3. Add environment variables.
4. Railway will automatically detect the `Procfile` and bind to `$PORT`.

---

## 5. Backend Environment Variables Reference

Configure these in the Render / Railway environment settings:

| Variable | Description | Example / Required |
|---|---|---|
| `ENVIRONMENT` | Runtime environment identifier | `production` |
| `PORT` | Bound port assigned by cloud platform | `$PORT` (auto-set by platform) |
| `HOST` | Network interface to bind | `0.0.0.0` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `https://gfd-challenge.vercel.app` |
| `DATABASE_URL` | Direct connection string with SSL | `postgresql://postgres:pwd@db.xxx.supabase.co:5432/postgres?sslmode=require` |
| `SUPABASE_URL` | Supabase Cloud project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Supabase anonymous public key | `eyJhbGci...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role secret key | `eyJhbGci...` |
| `GEMINI_API_KEY` | Google Gemini AI Studio API key | `AIzaSy...` |
| `GEMINI_MODEL` | Default Gemini model | `gemini-1.5-flash` |
| `ADMIN_API_KEY` | Secret token to secure `/refresh` and batch jobs | Set a random 32+ char secret |
| `STORAGE_IMAGE_BUCKET` | Image storage bucket | `citizen-images` |
| `STORAGE_AUDIO_BUCKET` | Audio storage bucket | `citizen-audio` |

---

## 6. Frontend Deployment (Vercel)

### 6.1 Deployment Steps
1. Connect the GitHub repository to [Vercel](https://vercel.com).
2. Configure Project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add the SPA rewrite file `frontend/vercel.json` (already created in repository).

### 6.2 Frontend Environment Variables
Set these under **Project Settings > Environment Variables** in Vercel:

| Variable | Value Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | HTTPS URL of the deployed backend on Render/Railway | `https://gfd-challenge-backend.onrender.com` |
| `VITE_SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon public key | `eyJhbGci...` |

> [!CAUTION]
> **NEVER** add `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `DATABASE_URL` to Vercel environment variables. All AI and privileged operations are handled strictly on the backend.

---

## 7. Connecting Frontend & Backend (CORS)

Once the frontend is deployed to Vercel (e.g. `https://gfd-challenge-app.vercel.app`):
1. Go to your Render / Railway backend settings.
2. Update `CORS_ORIGINS` to include your Vercel domain:
   ```env
   CORS_ORIGINS=https://gfd-challenge-app.vercel.app,http://localhost:5173
   ```
3. Trigger a backend redeploy to apply the updated CORS origin policy.

---

## 8. Deployment Verification (Smoke Test)

Run the included automated smoke test script from your local machine against the deployed backend:

```bash
python scripts/smoke_test.py https://gfd-challenge-backend.onrender.com
```

Expected output:
```text
======================================================================
 GFD CHALLENGE — PRODUCTION SMOKE TEST SUITE
 Target Backend: https://gfd-challenge-backend.onrender.com
======================================================================
[ PASS ] 1. Root Gateway Status -> / (HTTP 200)
[ PASS ] 2. Service Health Check -> /health (HTTP 200)
[ PASS ] 3. API OpenAPI Documentation -> /docs (HTTP 200)
[ PASS ] 4. District Infrastructure Intelligence (Read-Only) -> /api/infrastructure/districts (HTTP 200)
[ PASS ] 5. Decision-Support Gap Signals (Read-Only) -> /api/infrastructure/gap-signals (HTTP 200)
[ PASS ] 6. Request Clusters Registry (Read-Only) -> /api/intelligence/clusters (HTTP 200)
[ PASS ] 7. Emerging Issue Trends (Read-Only) -> /api/intelligence/emerging-issues (HTTP 200)
======================================================================
 RESULT: ALL SMOKE TESTS PASSED — BACKEND IS DEPLOYMENT-READY.
======================================================================
```

---

## 9. Troubleshooting & Common Issues

| Issue | Root Cause | Solution |
|---|---|---|
| **Health endpoint returns 503** | Backend cannot connect to Supabase PostgreSQL | Ensure `sslmode=require` is in `DATABASE_URL`. Check that the database password has no unencoded special characters. |
| **CORS error in browser console** | Deployed Vercel URL not in backend `CORS_ORIGINS` | Add full Vercel URL (e.g. `https://your-app.vercel.app`) to `CORS_ORIGINS` on backend and redeploy. |
| **Storage upload fails (403/401)** | User is not authenticated or storage path owner mismatch | Ensure user is signed in with Supabase Auth. Paths must follow `{user_id}/{request_id}/{filename}`. |
| **AI analysis returns degraded** | `GEMINI_API_KEY` missing or invalid | Ensure key is set in backend environment variables. Check API quota on Google AI Studio. |
| **Render cold starts (50-second delay)** | Free tier spin-down after 15 min inactivity | Render free tier puts services to sleep; wait 30-50s on initial load or upgrade to starter instance. |
