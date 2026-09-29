# GFD Challenge — Manual Testing Plan

This document outlines the human test cases to be performed on the deployed production application.  
All test results should be recorded in [`docs/manual_test_results.md`](file:///d:/College/Projects/GFD%20Challenge/docs/manual_test_results.md).

---

## Group A — Authentication

### A1: Citizen Sign Up
- **Preconditions**: User is on the deployed site (`https://your-frontend.vercel.app`) and logged out.
- **Steps**:
  1. Click **Sign In / Sign Up** in the navigation header.
  2. Select **Create an account**.
  3. Enter a valid email (`test-citizen@example.com`) and secure password (`P@ssw0rd123!`).
  4. Click **Sign Up**.
- **Expected Result**: Account is created. If Supabase email verification is enabled, a confirmation prompt is shown; if disabled, user is immediately signed in and their email appears in the header.

### A2: Citizen Sign In
- **Steps**:
  1. Open the login modal.
  2. Enter credentials of an existing account.
  3. Click **Sign In**.
- **Expected Result**: User session is established, auth modal closes, citizen portal loads with the user's past submission history.

### A3: Invalid Login Credentials
- **Steps**:
  1. Open login modal.
  2. Enter valid email with an incorrect password.
  3. Click **Sign In**.
- **Expected Result**: Clear error message is displayed (e.g., "Invalid login credentials"). No application crash, modal remains open.

### A4: Sign Out
- **Steps**:
  1. Click the **Sign Out** button in the header.
- **Expected Result**: Active session is destroyed. Protected state is cleared. User cannot view personal submission history until logging back in.

---

## Group B — Text Grievance Submission

### B1: English Text Submission
- **Input**:
  - Category: `Healthcare`
  - Text: `There is no proper hospital near our village. We have to travel more than 20 km for emergency treatment.`
  - District / Location: Select a location or pin on map (e.g. Coimbatore or Bengaluru).
- **Steps**: Click **Submit Request**.
- **Expected Result**:
  - Request successfully submitted with HTTP 201.
  - Success screen shows unique tracking UUID.
  - Canonical district is resolved automatically via PostGIS.
  - Request appears in the citizen history drawer.

### B2: Tamil Text Submission
- **Input**:
  - Category: `Healthcare`
  - Language: `Tamil`
  - Text: `எங்கள் கிராமத்தில் மருத்துவமனை வசதி இல்லை. அவசர சிகிச்சைக்காக 20 கிலோமீட்டர் பயணம் செய்ய வேண்டியுள்ளது.`
- **Steps**: Submit request and trigger AI analysis.
- **Expected Result**:
  - Request is saved with Tamil text intact.
  - Gemini AI analysis identifies language as `Tamil` (`ta`).
  - English translation is accurately generated preserving medical emergency details.
  - Category is classified as `Healthcare`.

### B3: Hindi Text Submission
- **Input**:
  - Category: `Water`
  - Language: `Hindi`
  - Text: `हमारे गांव में पिछले दो हफ्तों से पीने का पानी नहीं आ रहा है। हैंडपंप भी खराब पड़ा है।`
- **Steps**: Submit request and trigger AI analysis.
- **Expected Result**:
  - Submission succeeds.
  - AI detects Hindi (`hi`), translates faithfully into English, classifies category as `Water`, and tags urgency appropriately.

---

## Group C — Input Validation & Bounds

### C1: Empty Description
- **Steps**: Clear description text and attempt to submit.
- **Expected Result**: Form validation prevents submission with prompt "Description must be at least 10 characters".

### C2: Very Short Description (<10 characters)
- **Input**: `Bad road`
- **Expected Result**: Rejected by frontend and backend validation with clear error message.

### C3: Invalid Attachment File Type
- **Steps**: Attempt to upload a `.pdf`, `.exe`, or `.zip` file in the image uploader.
- **Expected Result**: File selection is rejected or flagged with error "Invalid file type. Please upload JPEG, PNG, or WebP images."

### C4: Oversized Image Upload (>10 MB)
- **Steps**: Select an image file exceeding 10 MB.
- **Expected Result**: Upload rejected client-side with alert: "File size exceeds 10 MB limit."

### C5: Oversized Audio Recording (>25 MB)
- **Steps**: Attempt to upload an audio file exceeding 25 MB.
- **Expected Result**: Rejected with alert: "Audio file exceeds 25 MB limit."

---

## Group D — Visual Inspection (Computer Vision)

### D1: Road Damage / Pothole Inspection
- **Steps**:
  1. Attach a photo showing asphalt potholes or road cracks.
  2. Enter description: `Severe road damage with deep potholes on main bus route.`
  3. Submit and view AI Insight drawer.
- **Expected Result**:
  - Image is securely stored in private bucket `citizen-images`.
  - Gemini vision model inspects the image.
  - Visual observations list 1–5 concrete physical findings (e.g. "Surface asphalt erosion", "Pothole depth ~15cm").
  - Analysis does NOT hallucinate details not visible in the photo.

---

## Group E — Voice Recording & Transcription

### E1: Voice Recording in English
- **Steps**:
  1. Click **Start Recording** in the voice recorder widget.
  2. Speak: `Our village does not have a proper drinking water supply. The pipeline broke 3 days ago.`
  3. Click **Stop Recording**, verify playback, and submit.
- **Expected Result**:
  - Audio blob recorded via Web Audio MediaRecorder API.
  - Uploaded to private `citizen-audio` bucket under `{user_id}/{request_id}/`.
  - Gemini transcribes speech into text matching spoken words.

### E2: Voice Recording in Tamil
- **Steps**:
  1. Record 10 seconds of speech in Tamil regarding electricity cuts.
  2. Submit request.
- **Expected Result**:
  - Voice recording preserved.
  - Accurate Tamil speech transcription and corresponding English translation generated in AI analysis card.

---

## Group F — AI Resilience & Graceful Fallback

### F1: AI Service Unavailable / Invalid Key Fallback
- **Steps**:
  1. Submit a valid citizen request while backend AI service is simulating quota exhaustion or unconfigured key.
- **Expected Result**:
  - Citizen request submission succeeds and remains 100% intact in the database.
  - AI processing state is marked as `failed` or `pending`.
  - Frontend displays a non-blocking advisory note: "AI analysis temporarily unavailable; your request has been recorded for review."
  - Backend API does NOT crash or return a 500 unhandled exception.

---

## Group G — Request Intelligence (Similarity & Duplicates)

### G1: Similar & Duplicate Grievance Detection
- **Steps**:
  1. Citizen A submits: `There is no drinking water supply in Ward 4, pump is broken.`
  2. Citizen B submits in the same ward: `Ward 4 has had no drinking water for three days due to broken pump.`
  3. Citizen C submits in a different district: `There is no drinking water supply in our village.`
  4. Citizen D submits: `Streetlights are not functioning on 5th cross road.`
- **Expected Result**:
  - Citizen A and B in the same district/coordinates are identified as **duplicates** (`relationship_type: duplicate`).
  - Citizen C in a different district is identified as **similar** (`relationship_type: similar`).
  - Citizen D is recognized as a different issue.
  - Requests are grouped into an explainable cluster with deterministic summary.

---

## Group H — Emerging Issues & Surge Detection

### H1: Grievance Surge Acceleration
- **Steps**:
  1. Query `/api/intelligence/emerging-issues?window_days=7`.
- **Expected Result**:
  - Returns accelerating grievance topics comparing current 7-day volume against previous 7-day volume.
  - Transparent growth percentage is computed (no division by zero if prior count was 0).
  - Acceleration badges indicate sudden demand spikes.

---

## Group I — District Infrastructure Intelligence

### I1: Multi-Sector Infrastructure Benchmarking
- **Steps**:
  1. Open District Intelligence view for a canonical district (e.g. Bengaluru Urban or Coimbatore).
  2. Inspect Healthcare, Water, and Education tabs.
- **Expected Result**:
  - Census 2011 population displayed with explicit provenance note.
  - Per-capita normalizations rendered (Facilities/100k, Beds/10k, Doctors/10k, Requests/10k).
  - Cross-district percentiles shown (e.g., P85 Demand Rank vs P20 Infrastructure Rank).
  - Explainable Gap Signal displayed with neutral label (`potential_gap`, `infrastructure_pressure`, `balanced`).
  - Transparent provenance metadata list identifies Census 2011, HMIS, NFHS-5, and synthetic investment flags.

---

## Group J — Citizen Privacy & Data Isolation

### J1: Multi-Tenant Citizen Isolation
- **Steps**:
  1. Citizen A logs in and submits Request #1 with an image.
  2. Citizen B logs in from a different browser or incognito window.
  3. Citizen B views their submission history.
  4. Citizen B attempts to access Request #1 directly via `/api/requests/{id}?user_id={Citizen_B_ID}`.
  5. Citizen B attempts to directly download Citizen A's image storage URL.
- **Expected Result**:
  - Citizen B's history shows ONLY Citizen B's requests.
  - Direct API access to Citizen A's request returns HTTP 403 Forbidden.
  - Direct access to Citizen A's private storage path returns HTTP 403 / 401 Unauthorized.
  - Aggregate infrastructure endpoints contain zero citizen PII (no names, phone numbers, or user IDs).

---

## Group K — Mobile Usability & Responsiveness

### K1: Viewport & Touch Controls
- **Steps**: Open deployed application on mobile device (or Chrome DevTools mobile view - iPhone 14 / Pixel 7).
- **Check**:
  - Navigation bar collapses cleanly or fits without clipping.
  - Form fields, buttons, and textarea are easily tappable (min 44px touch targets).
  - Audio recording controls are operable on mobile.
  - Location picker map is usable with touch pan/zoom.
  - Cards do not overflow horizontally.

---

## Group L — Network Resilience & Error Handling

### L1: Network Disruption & Throttling
- **Steps**:
  1. In Chrome DevTools, set Network to **Slow 3G**.
  2. Submit a request and observe loading spinners and button disable states.
  3. Turn off network connection (Offline) and attempt an action.
- **Expected Result**:
  - Button shows loading state and prevents double submission.
  - When offline, a clear error banner appears ("Network error. Please check your connection").
  - Application does NOT crash or render a white screen.
