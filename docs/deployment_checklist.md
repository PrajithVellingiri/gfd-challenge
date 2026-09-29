# Production Deployment Checklist

Use this checklist during and after deployment to ensure complete operational readiness and security.

---

## 1. Backend Verification

- [ ] **Deploy Successful**: Render / Railway build succeeded and container is running.
- [ ] **Process Binding**: FastAPI is bound to `0.0.0.0` and using dynamic platform `$PORT`.
- [ ] **Health Endpoint Works**: `GET /health` returns HTTP 200 with status `"healthy"`.
- [ ] **Database Connected**: Backend successfully queries Supabase PostgreSQL over SSL.
- [ ] **Supabase SDK Initialized**: Supabase Client initializes with URL and service role key.
- [ ] **Gemini Connected**: `GEMINI_API_KEY` is loaded on backend only; multimodal analysis functions.
- [ ] **CORS Restricted**: Allowed origins set strictly to the deployed Vercel domain (not wildcard `*` with credentials).
- [ ] **Auth Token Validation**: Bearer token or User ID authorization works for citizen submissions and history queries.
- [ ] **Storage Buckets Private**: `citizen-images` and `citizen-audio` are confirmed private in Supabase console.
- [ ] **Admin Endpoints Protected**: `/api/infrastructure/refresh` and `/api/intelligence/process-pending` reject anonymous calls.

---

## 2. Frontend Verification

- [ ] **Vercel Deployment Successful**: Build succeeded (`npm run build`) without errors or warnings.
- [ ] **API URL Configured**: `VITE_API_BASE_URL` points to the HTTPS backend endpoint on Render / Railway.
- [ ] **Supabase SDK Configured**: `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` configured in Vercel environment.
- [ ] **SPA Rewrites Active**: Navigating directly to subpaths does not 404 (`vercel.json` rewrites to `/index.html`).
- [ ] **Sign Up / Login Works**: Citizen can create an account or sign in with email and password.
- [ ] **Citizen Portal Loads**: Form renders categories, language selector, text input, audio recorder, and file uploader.
- [ ] **History Loads**: Citizen request history fetches only the authenticated citizen's submissions.
- [ ] **Infrastructure Cards Render**: Demand metrics, infrastructure supply, percentiles, and gap signals render clearly.

---

## 3. Security & Compliance Verification

- [ ] **Zero Secrets in Git**: No `.env`, service role keys, database passwords, or Gemini keys committed to GitHub.
- [ ] **Zero Secrets in Frontend Bundle**: Inspected `dist/assets/*.js` to ensure no database passwords or Gemini keys are bundled.
- [ ] **Row Level Security (RLS) Active**: RLS enabled on all 8 tables (`users`, `districts`, `citizen_requests`, `infrastructure`, `demographics`, `investments`, `ai_analyses`, `district_intelligence`).
- [ ] **Storage Path Isolation**: Files stored under `{user_id}/{request_id}/{filename}` and cannot be accessed by other citizens.
- [ ] **Privacy Guarantees**: Aggregate endpoints (`/api/infrastructure/*`, `/api/intelligence/clusters`) leak zero citizen PII.

---

## 4. Operational Sign-Off

| Checkpoint | Status | Verified By | Date / Time |
|---|---|---|---|
| Automated Backend Tests (104/104) | Passed | Test Runner | 2026-09-29 |
| Automated Frontend Tests & Build | Passed | Vite & Node Test | 2026-09-29 |
| Secret & Gitignore Audit | Passed | Git Grep Audit | 2026-09-29 |
| Production Smoke Test Script | Ready | `scripts/smoke_test.py` | 2026-09-29 |
| Live Smoke Test | Pending Deployment | User / Operator | — |
| Manual Testing Plan Execution | Pending Deployment | User / Operator | — |
