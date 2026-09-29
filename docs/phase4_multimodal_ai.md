# Phase 4 — Multimodal AI Intelligence

## 1. Overview & Objective

Phase 4 introduces automated, multimodal AI intelligence to the **GFD Challenge DPI Platform**. Leveraging Google's Gemini models (`gemini-1.5-flash`), raw citizen grievances submitted in any modality (text descriptions, voice notes, or site photos) are converted into structured, actionable intelligence for digital governance triage.

### What Phase 4 Implements:
1. **Multilingual Understanding & Translation**: Identifies input language (English, Tamil, Hindi, etc.) and produces accurate English translations while preserving local names, village context, and nuances.
2. **Canonical Category Classification**: Normalizes requests strictly into one of 8 official DPI sectors:
   - `Healthcare`
   - `Education`
   - `Roads`
   - `Water`
   - `Transportation`
   - `Electricity`
   - `Digital Infrastructure`
   - `Other`
3. **Sub-Category & Urgency Assessment**: Extracts granular sub-categories (e.g., *PHC Doctor Shortage*, *Pothole Cluster*, *Piped Water Contamination*) and urgency ratings (`Low`, `Medium`, `High`, `Critical`).
4. **Speech-to-Text Transcription**: Faithfully transcribes in-browser recorded audio notes into text and translates them to English.
5. **Computer Vision Inspection**: Analyzes field photos, identifies infrastructure types, extracts 1–5 objective visual observations, and assesses visible physical severity.
6. **Executive Summarization & Keywords**: Produces concise summaries (<=200 chars) and 3–10 infrastructure keywords for rapid search and indexing.
7. **Prompt Versioning & Traceability**: Enforces `prompt_version = "v1.0"` across all analyses.
8. **Conservative Confidence Reporting**: Does not fabricate confidence scores; confidence remains `null` when not officially reported by the model.

### Explicit Phase Boundaries (Deferred to Later Phases):
- **Deferred to Phase 5**: Semantic vector embeddings (768-dim), semantic duplicate detection, request clustering.
- **Deferred to Phase 6**: Spatial hotspot density estimation, infrastructure gap scoring, ML priority scoring.
- **Deferred to Phase 7**: Recommendation generation and policymaker decision dashboard.

---

## 2. Architecture & Data Flow

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

---

## 3. Database Schema Enhancements (Migration 005)

Migration `backend/migrations/005_ai_analyses_enhancements.sql` adds the following columns to `public.ai_analyses`:

| Column | Type | Description |
| :--- | :--- | :--- |
| `prompt_version` | `VARCHAR(50)` | Version identifier (default: `'v1.0'`) |
| `category` | `VARCHAR(100)` | Canonical category classification |
| `sub_category` | `VARCHAR(150)` | Descriptive sub-sector |
| `urgency` | `VARCHAR(50)` | Urgency level (`Low`, `Medium`, `High`, `Critical`) |
| `summary` | `TEXT` | Concise summary (<=200 characters) |
| `keywords` | `JSONB` | Array of 3–10 keywords |
| `transcript` | `TEXT` | Spoken audio transcript |
| `image_analysis` | `JSONB` | Visual observations and severity |
| `processing_status` | `VARCHAR(50)` | Status (`pending`, `processing`, `completed`, `failed`) |
| `error_message` | `TEXT` | Error details if processing failed |
| `updated_at` | `TIMESTAMPTZ` | Timestamp of last modification |

Indexes added:
- `idx_ai_analyses_processing_status` on `(processing_status)`
- `idx_ai_analyses_category` on `(category)`

---

## 4. API Endpoints

### 4.1 Trigger Analysis
- **URL**: `POST /api/requests/{request_id}/analyze`
- **Headers**: `X-User-Id: <UUID>`
- **Description**: Triggers multimodal analysis on a citizen request. Enforces ownership authorization.
- **Response**: `200 OK`
```json
{
  "request_id": "c09ba966-70d2-48db-8613-76971caba337",
  "prompt_version": "v1.0",
  "detected_language": "Tamil",
  "translated_text": "Drinking water pipeline broke near the village square.",
  "category": "Water",
  "sub_category": "Piped Drinking Water Supply",
  "urgency": "High",
  "summary": "Broken drinking water pipeline causing acute water shortage.",
  "keywords": ["drinking water", "pipeline break", "water shortage"],
  "transcript": null,
  "image_analysis": {},
  "confidence": null,
  "processing_status": "completed",
  "error_message": null
}
```

### 4.2 Retrieve Existing Analysis
- **URL**: `GET /api/requests/{request_id}/analysis`
- **Headers**: `X-User-Id: <UUID>`
- **Description**: Retrieves existing AI analysis for a request. Returns `404 Not Found` if not yet analyzed.

### 4.3 Direct Text Analysis (Live Preview / Testing)
- **URL**: `POST /api/ai/analyze-text`
- **Body**: `{"text": "Severe water leakage on Main St."}`
- **Description**: Live text preview of language detection, translation, category, urgency, and keywords.

---

## 5. Resilience & Fault Tolerance

1. **Missing API Key**: If `GEMINI_API_KEY` is unset or empty, `processing_status` transitions to `'failed'` with `error_message = 'Google Gemini API key is not configured in backend environment.'`. The underlying citizen request remains completely intact.
2. **API Timeout or Rate Limit**: Any Gemini service exceptions are caught cleanly; status transitions to `'failed'` without crashing the FastAPI process.
3. **Offline Test Isolation**: All 60 automated tests use mocked Gemini responses, enabling deterministic testing with zero real API calls or secret requirements.
4. **Advisory Notice**: All UI components display a clear disclaimer: *"AI analysis provides automated decision-support triage for digital public infrastructure and does not replace official on-ground inspection."*
