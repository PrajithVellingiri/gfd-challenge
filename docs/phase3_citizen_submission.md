# Phase 3: Citizen Submission System

## 1. Overview & Citizen Workflow
Phase 3 implements the citizen-facing grievance submission system for the GFD Challenge Digital Public Infrastructure (DPI) platform. Citizens can submit localized infrastructure needs and service gaps via text, optional photo uploads, and optional voice notes, with automatic PostGIS-based district containment resolution.

```
Citizen
   ↓
Sign In / Quick Demo Session
   ↓
Fill Request (Description, Category, Language, Urgency)
   ↓
Optional Media (Image <10MB, Voice <25MB)
   ↓
Location (Browser GPS or Manual District Selection)
   ↓
Client-Side Validation
   ↓
FastAPI Backend (/api/requests)
   ↓
PostGIS Point-in-Polygon District Resolution
   ↓
Supabase PostgreSQL + Storage
   ↓
Submission Confirmation (REQ-XXXX)
   ↓
Citizen Request History
```

---

## 2. API Endpoints

| Method | Endpoint | Description | Auth / Security |
|---|---|---|---|
| `POST` | `/api/requests` | Creates citizen request, validates ownership & media, resolves district | Authenticated citizen |
| `GET` | `/api/requests` | Returns authenticated citizen's own submitted requests | Isolated to requesting citizen |
| `GET` | `/api/requests/{id}` | Retrieves request details if user is authorized | 403 Forbidden on cross-user access |
| `POST` | `/api/requests/upload` | Validates file size & MIME type, uploads attachment to Supabase Storage | Authenticated citizen |
| `POST` | `/api/requests/storage-path` | Generates deterministic isolated storage path `{user_id}/{request_id}/{filename}` | Authenticated citizen |

### Standard Response Format
```json
{
  "success": true,
  "request_id": "8fa816e8-2cb6-41bf-bb78-3a05c6d3bc0a",
  "status": "submitted",
  "district_id": "a3b8d142-76e9-4e02-8a9d-5f8e12c4b789",
  "district_name": "Bengaluru Urban",
  "message": "Request submitted successfully. Your development request has been recorded."
}
```

---

## 3. Media Upload Specifications

### Image Uploads
- **Target Bucket**: `citizen-images` (Private)
- **Supported MIME Types**: `image/jpeg`, `image/png`, `image/webp`
- **Max File Size**: 10 MB
- **Path Isolation**: `{user_id}/{request_id}/{filename}`
- Direct binary storage in PostgreSQL is strictly prohibited; only relative storage paths are stored in the database.

### Voice Recordings
- **Target Bucket**: `citizen-audio` (Private)
- **API**: Browser `MediaRecorder` API
- **Supported MIME Types**: `audio/webm`, `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`, `audio/x-m4a`
- **Max File Size**: 25 MB
- Audio playback, timer feedback, and re-record controls are built into the citizen interface.

---

## 4. PostGIS District Resolution
When coordinates are supplied (`latitude`, `longitude`):
1. The backend executes a spatial containment query:
   ```sql
   SELECT id, name, state FROM public.districts
   WHERE boundary IS NOT NULL AND ST_Contains(boundary, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326))
   LIMIT 1;
   ```
2. If the cloud database is offline during testing, a spatial fallback verifies the coordinate using Shapely against the authoritative boundary dataset.
3. Coordinates falling outside all known district polygons remain valid with `district_id = null`, preserving the citizen's exact submission without assigning an inaccurate district.

---

## 5. Local Development & Testing

### Running Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Running Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the Citizen Submission Portal.

### Running Full Automated Test Suite
```bash
# Backend pytest suite (40 tests covering Phase 1, 2, and 3)
python -m pytest -v

# Frontend component & validation test suite
cd frontend && npm test
```
