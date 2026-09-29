# GFD Challenge — Manual Test Results Log

This document records the human execution results of the manual testing plan on the deployed live application.

---

## 1. Test Execution Summary

| Metric | Value |
|---|---|
| **Total Test Cases Planned** | 22 |
| **Executed** | Ready for Live Run |
| **Passed** | — |
| **Failed** | — |
| **Blocked** | — |
| **Critical Issues** | 0 |
| **High Issues** | 0 |
| **Medium Issues** | 0 |
| **Low Issues** | 0 |

---

## 2. Test Execution Log

| ID | Test Case | Expected Result | Result | Severity | Notes |
|---|---|---|---|---|---|
| **M01** | A1: Citizen Sign Up | Account created, session established or confirmation prompted | Pending Live Run | - | Pre-deployment verified via mock & unit tests |
| **M02** | A2: Citizen Sign In | Access citizen portal, user email in navbar | Pending Live Run | - | Ready for live verification |
| **M03** | A3: Invalid Login | Error shown, no crash, modal remains open | Pending Live Run | - | Ready for live verification |
| **M04** | A4: Sign Out | Session cleared, user history hidden | Pending Live Run | - | Ready for live verification |
| **M05** | B1: English Text Submission | Request stored, district resolved, appears in history | Pending Live Run | - | PostGIS resolution verified |
| **M06** | B2: Tamil Text Submission | Tamil preserved, AI detects language and translates to English | Pending Live Run | - | Multilingual prompt verified |
| **M07** | B3: Hindi Text Submission | Hindi preserved, category and urgency classified | Pending Live Run | - | Translation pipeline verified |
| **M08** | C1: Empty Description | Validation prevents submit, shows helpful error | Pending Live Run | - | Frontend validation verified |
| **M09** | C2: Short Description (<10 chars) | Blocked with "Description must be at least 10 chars" | Pending Live Run | - | Pydantic & form validation verified |
| **M10** | C3: Invalid Attachment Type (.exe/.zip) | Rejected client-side with clear warning | Pending Live Run | - | MIME validation verified |
| **M11** | C4: Oversized Image (>10 MB) | Blocked with 10 MB limit alert | Pending Live Run | - | 10 MB bound verified |
| **M12** | C5: Oversized Audio (>25 MB) | Blocked with 25 MB limit alert | Pending Live Run | - | 25 MB bound verified |
| **M13** | D1: Road Damage / Vision Analysis | Image uploaded, 1-5 objective observations shown | Pending Live Run | - | Gemini 1.5 vision prompt verified |
| **M14** | E1: English Voice Recording | Audio recorded, transcript matches speech | Pending Live Run | - | MediaRecorder API verified |
| **M15** | E2: Tamil Voice Recording | Tamil speech transcribed and translated | Pending Live Run | - | Multimodal audio pipeline verified |
| **M16** | F1: AI Failure Resilience | Citizen request intact, AI marked failed, no 500 error | Pending Live Run | - | Graceful error boundary verified |
| **M17** | G1: Request Similarity & Duplicates | Same ward = duplicate; different district = similar | Pending Live Run | - | pgvector cosine similarity verified |
| **M18** | H1: Emerging Issues Surge Detection | Period-over-period growth calculated without div-by-zero | Pending Live Run | - | Window growth math verified |
| **M19** | I1: District Infrastructure Benchmarks | Population, per-capita ratios, percentiles, provenance | Pending Live Run | - | Census 2011/HMIS benchmarks verified |
| **M20** | J1: Multi-Tenant Citizen Privacy | Citizen A cannot access Citizen B's request or files | Pending Live Run | - | Supabase RLS & owner check verified |
| **M21** | K1: Mobile Viewport & Touch Controls | Responsive on mobile, min 44px tap targets, map operable | Pending Live Run | - | Tailwind responsive classes verified |
| **M22** | L1: Network Disruption & Throttling | Disabled button during submit, graceful offline banner | Pending Live Run | - | Network resilience verified |

---

## 3. Discovered Defects & Fixes

*(Issues identified during live manual testing will be logged here with reproduction steps, severity, and resolution commit).*

| Defect ID | Associated Test | Description | Severity | Status | Fix Commit |
|---|---|---|---|---|---|
| *None* | — | No defects logged prior to live deployment execution | — | Closed | — |
