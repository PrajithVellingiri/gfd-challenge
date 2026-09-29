"""
Automated Test Suite for Phase 4: Multimodal AI Intelligence.
Validates:
- Migration 005 schema enhancements for public.ai_analyses
- Google Gemini client wrapper and API error handling
- Markdown fence stripping, JSON cleaning, and schema validators
- Canonical category and urgency normalization
- Multilingual analysis (English, Tamil, Hindi)
- Speech-to-text audio transcription and analysis flow
- Vision inspection and physical observation analysis flow
- Master RequestAnalyzer orchestration across multimodal inputs
- Graceful degradation and failure handling (missing key, timeout, error)
- FastAPI endpoints (/api/requests/{id}/analyze, /api/requests/{id}/analysis, /api/ai/analyze-text)
- Authorization and anti-leakage checks
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.gemini_client import GeminiClient, GeminiAPIError
from app.services.ai.prompt_templates import PROMPT_VERSION, TEXT_ANALYSIS_SYSTEM_PROMPT, IMAGE_ANALYSIS_PROMPT, AUDIO_ANALYSIS_PROMPT
from app.services.ai.validators import (
    clean_gemini_json_response,
    normalize_category,
    normalize_urgency,
    ALLOWED_CATEGORIES,
    ALLOWED_URGENCIES,
    TextAnalysisResult,
    ImageAnalysisResult,
    AudioAnalysisResult,
    AIRequestAnalysisResponse,
)
from app.services.ai.image_analyzer import ImageAnalyzer
from app.services.ai.audio_analyzer import AudioAnalyzer
from app.services.ai.request_analyzer import RequestAnalyzer

client = TestClient(app)
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


# =============================================================================
# 1. Migration 005 Verification
# =============================================================================

def test_migration_005_sql_schema():
    """Verify migration 005 adds all required AI intelligence columns and indexes."""
    migration_file = MIGRATIONS_DIR / "005_ai_analyses_enhancements.sql"
    assert migration_file.exists(), "Migration 005 file is missing!"

    sql = migration_file.read_text(encoding="utf-8").lower()
    required_columns = [
        "prompt_version",
        "category",
        "sub_category",
        "urgency",
        "summary",
        "keywords",
        "transcript",
        "image_analysis",
        "processing_status",
        "error_message",
        "updated_at",
    ]
    for col in required_columns:
        assert col in sql, f"Migration 005 missing column '{col}'"

    # Status check constraint
    assert "pending" in sql and "processing" in sql and "completed" in sql and "failed" in sql
    # Indexes
    assert "idx_ai_analyses_processing_status" in sql
    assert "idx_ai_analyses_category" in sql


# =============================================================================
# 2. JSON Cleaning and Response Sanitization
# =============================================================================

def test_clean_gemini_json_fences():
    """Verify clean_gemini_json_response strips markdown code fences and conversational preamble."""
    # Plain JSON
    raw_plain = '{"detected_language": "English", "category": "Roads"}'
    assert clean_gemini_json_response(raw_plain)["category"] == "Roads"

    # JSON with ```json ... ``` code fence
    raw_fenced = """```json
{
  "detected_language": "Tamil",
  "category": "Healthcare"
}
```"""
    assert clean_gemini_json_response(raw_fenced)["detected_language"] == "Tamil"

    # JSON with conversational preamble and trailing notes
    raw_conversational = """Here is the structured analysis requested:
```json
{
  "detected_language": "Hindi",
  "category": "Water"
}
```
Please let me know if you need more details!"""
    assert clean_gemini_json_response(raw_conversational)["category"] == "Water"

    # Invalid empty or non-JSON input raises ValueError
    with pytest.raises(ValueError):
        clean_gemini_json_response("")
    with pytest.raises(ValueError):
        clean_gemini_json_response("This is completely unparseable.")


# =============================================================================
# 3. Canonical Category and Urgency Normalization
# =============================================================================

def test_category_normalization():
    """Verify category normalization maps to canonical 8 categories or falls back to 'Other'."""
    for cat in ALLOWED_CATEGORIES:
        assert normalize_category(cat) == cat
        assert normalize_category(cat.lower()) == cat
        assert normalize_category(cat.upper()) == cat

    # Aliases
    assert normalize_category("hospital") == "Healthcare"
    assert normalize_category("pothole repair") == "Roads"
    assert normalize_category("drinking water supply") == "Water"
    assert normalize_category("broadband cable") == "Digital Infrastructure"
    assert normalize_category("power transformer") == "Electricity"
    assert normalize_category("bus service") == "Transportation"
    assert normalize_category("school facility") == "Education"

    # Unrecognized fallback
    assert normalize_category("spaceship landing") == "Other"
    assert normalize_category(None) == "Other"
    assert normalize_category("") == "Other"


def test_urgency_normalization():
    """Verify urgency normalization maps strictly to Low, Medium, High, Critical."""
    for urg in ALLOWED_URGENCIES:
        assert normalize_urgency(urg) == urg
        assert normalize_urgency(urg.lower()) == urg

    assert normalize_urgency("extreme") == "Medium"
    assert normalize_urgency(None) == "Medium"
    assert normalize_urgency("") == "Medium"


# =============================================================================
# 4. Multilingual Text Analysis (English, Tamil, Hindi)
# =============================================================================

def test_multilingual_text_analysis_english():
    """Test text analysis on an English healthcare grievance."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.api_key = "test_key"
    mock_gemini.generate_text.return_value = json.dumps({
        "detected_language": "English",
        "translated_text": "The Primary Health Centre lacks 24/7 doctors and emergency oxygen cylinders.",
        "category": "Healthcare",
        "sub_category": "Hospital Emergency Services",
        "urgency": "High",
        "summary": "Primary Health Centre in rural block lacks emergency staff and oxygen equipment.",
        "keywords": ["PHC", "doctor shortage", "oxygen cylinders", "emergency care"]
    })

    analyzer = RequestAnalyzer(gemini_client=mock_gemini)
    result = analyzer.analyze_text("The Primary Health Centre lacks 24/7 doctors and emergency oxygen cylinders.")

    assert result.detected_language == "English"
    assert result.category == "Healthcare"
    assert result.urgency == "High"
    assert len(result.keywords) >= 3


def test_multilingual_text_analysis_tamil():
    """Test text analysis on a Tamil water supply request."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.api_key = "test_key"
    mock_gemini.generate_text.return_value = json.dumps({
        "detected_language": "Tamil",
        "translated_text": "Drinking water pipeline has broken near the village square, causing water shortage.",
        "category": "Water",
        "sub_category": "Piped Drinking Water Supply",
        "urgency": "High",
        "summary": "Broken drinking water pipeline causing acute water shortage in village square.",
        "keywords": ["drinking water", "pipeline break", "water supply", "village square"]
    })

    analyzer = RequestAnalyzer(gemini_client=mock_gemini)
    tamil_input = "எங்கள் கிராமத்தில் குடிநீர் குழாய் உடைந்து ஒரு வாரமாக குடிநீர் விநியோகம் இல்லை."
    result = analyzer.analyze_text(tamil_input)

    assert result.detected_language == "Tamil"
    assert result.category == "Water"
    assert result.urgency == "High"
    assert "Drinking water pipeline" in result.translated_text


def test_multilingual_text_analysis_hindi():
    """Test text analysis on a Hindi road safety request."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.api_key = "test_key"
    mock_gemini.generate_text.return_value = json.dumps({
        "detected_language": "Hindi",
        "translated_text": "Main road connecting the market has severe potholes causing fatal accidents.",
        "category": "Roads",
        "sub_category": "Pothole Repair & Road Safety",
        "urgency": "Critical",
        "summary": "Severe potholes on main market road causing frequent accidents.",
        "keywords": ["road repair", "potholes", "market road", "accident hazard"]
    })

    analyzer = RequestAnalyzer(gemini_client=mock_gemini)
    hindi_input = "बाजार को जोड़ने वाली मुख्य सड़क पर बहुत बड़े गड्ढे हैं जिससे लगातार दुर्घटनाएं हो रही हैं।"
    result = analyzer.analyze_text(hindi_input)

    assert result.detected_language == "Hindi"
    assert result.category == "Roads"
    assert result.urgency == "Critical"


# =============================================================================
# 5. Image & Audio Analysis Validation & Processing
# =============================================================================

def test_image_analyzer_mime_and_size_validation():
    """Verify ImageAnalyzer rejects invalid MIME types and oversize payloads."""
    mock_gemini = MagicMock(spec=GeminiClient)
    analyzer = ImageAnalyzer(client=mock_gemini)

    # Empty payload
    with pytest.raises(ValueError, match="No image bytes provided"):
        analyzer.analyze_image(b"")

    # Unsupported MIME
    with pytest.raises(ValueError, match="Unsupported image MIME type"):
        analyzer.analyze_image(b"fake_pdf_content", mime_type="application/pdf")

    # Oversize payload (>10MB)
    large_payload = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="Image size exceeds limit"):
        analyzer.analyze_image(large_payload, mime_type="image/jpeg")


def test_image_analyzer_successful_visual_inspection():
    """Verify ImageAnalyzer extracts objective observations, infrastructure type, and severity."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.generate_vision.return_value = json.dumps({
        "image_relevant": True,
        "infrastructure_type": "Roads",
        "observations": [
            "Pothole visible across approximately half the road width",
            "Water accumulation visible within the depression",
            "Cracked asphalt edges along the perimeter"
        ],
        "severity": "High",
        "summary": "Substantial road crater with standing water obstructing single-lane traffic."
    })

    analyzer = ImageAnalyzer(client=mock_gemini)
    result = analyzer.analyze_image(b"valid_image_bytes", mime_type="image/jpeg")

    assert result.image_relevant is True
    assert result.infrastructure_type == "Roads"
    assert len(result.observations) == 3
    assert result.severity == "High"


def test_audio_analyzer_mime_and_size_validation():
    """Verify AudioAnalyzer rejects unsupported formats and oversize audio."""
    mock_gemini = MagicMock(spec=GeminiClient)
    analyzer = AudioAnalyzer(client=mock_gemini)

    with pytest.raises(ValueError, match="No audio bytes provided"):
        analyzer.analyze_audio(b"")

    with pytest.raises(ValueError, match="Unsupported audio MIME type"):
        analyzer.analyze_audio(b"fake_text", mime_type="text/plain")

    large_audio = b"0" * (26 * 1024 * 1024)
    with pytest.raises(ValueError, match="Audio size exceeds limit"):
        analyzer.analyze_audio(large_audio, mime_type="audio/webm")


def test_audio_analyzer_successful_transcription():
    """Verify AudioAnalyzer produces faithful transcript, translation, and category."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.generate_audio.return_value = json.dumps({
        "transcript": "எங்கள் கிராமத்திற்கு மின்சாரம் இரண்டு நாட்களாக இல்லை.",
        "detected_language": "Tamil",
        "translated_text": "There has been no electricity in our village for two days.",
        "category": "Electricity",
        "sub_category": "Village Power Outage",
        "urgency": "High",
        "summary": "Total power outage in village ongoing for two days.",
        "keywords": ["power cut", "electricity blackout", "transformer outage"]
    })

    analyzer = AudioAnalyzer(client=mock_gemini)
    result = analyzer.analyze_audio(b"audio_bytes", mime_type="audio/webm")

    assert "மின்சாரம்" in result.transcript
    assert result.detected_language == "Tamil"
    assert result.category == "Electricity"
    assert result.urgency == "High"


# =============================================================================
# 6. Master RequestAnalyzer Multimodal Orchestration
# =============================================================================

def test_request_analyzer_full_multimodal_flow():
    """Verify master orchestrator coordinates text, audio transcript, and vision inspection."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.api_key = "test_key"

    # Mock text call
    mock_gemini.generate_text.return_value = json.dumps({
        "detected_language": "English",
        "translated_text": "Collapsed culvert on rural connecting road.",
        "category": "Roads",
        "sub_category": "Culvert Collapse",
        "urgency": "Critical",
        "summary": "Collapsed culvert blocking vehicular access between villages.",
        "keywords": ["culvert", "road collapse", "rural connectivity", "bridge"]
    })

    # Mock audio call
    mock_gemini.generate_audio.return_value = json.dumps({
        "transcript": "Heavy rain caused the culvert to break completely.",
        "detected_language": "English",
        "translated_text": "Heavy rain caused the culvert to break completely.",
        "category": "Roads",
        "sub_category": "Culvert Collapse",
        "urgency": "Critical",
        "summary": "Culvert collapse from heavy rains.",
        "keywords": ["rain damage", "culvert"]
    })

    # Mock vision call
    mock_gemini.generate_vision.return_value = json.dumps({
        "image_relevant": True,
        "infrastructure_type": "Roads",
        "observations": [
            "Concentric fracture in masonry culvert arch",
            "Roadbed washaway visible on left shoulder"
        ],
        "severity": "Critical",
        "summary": "Structural failure of stone culvert with roadbed collapse."
    })

    orchestrator = RequestAnalyzer(gemini_client=mock_gemini)
    result = orchestrator.analyze_citizen_request(
        request_id=uuid4(),
        description="Collapsed culvert on rural connecting road.",
        audio_bytes=b"sample_audio",
        audio_mime="audio/webm",
        image_bytes=b"sample_image",
        image_mime="image/jpeg"
    )

    assert result["processing_status"] == "completed"
    assert result["prompt_version"] == "v1.0"
    assert result["category"] == "Roads"
    assert result["urgency"] == "Critical"
    assert result["transcript"] == "Heavy rain caused the culvert to break completely."
    assert "observations" in result["image_analysis"]
    assert len(result["image_analysis"]["observations"]) == 2
    # Verify confidence is NOT fabricated (must be None)
    assert result["confidence"] is None


def test_request_analyzer_graceful_missing_api_key():
    """Verify analyzer gracefully marks request 'failed' with error_message if API key missing."""
    client_no_key = GeminiClient(api_key=None)
    orchestrator = RequestAnalyzer(gemini_client=client_no_key)

    result = orchestrator.analyze_citizen_request(
        request_id=uuid4(),
        description="Potholes on road."
    )

    assert result["processing_status"] == "failed"
    assert "API key is not configured" in result["error_message"]
    assert result["category"] == "Other"


def test_request_analyzer_graceful_api_failure():
    """Verify analyzer handles network or Gemini API exceptions gracefully without crashing."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_gemini.api_key = "test_key"
    mock_gemini.generate_text.side_effect = GeminiAPIError("503 Service Unavailable / Rate Limit Exceeded")

    orchestrator = RequestAnalyzer(gemini_client=mock_gemini)
    result = orchestrator.analyze_citizen_request(
        request_id=uuid4(),
        description="Potholes on road."
    )

    assert result["processing_status"] == "failed"
    assert "503 Service Unavailable" in result["error_message"]


# =============================================================================
# 7. FastAPI Endpoints Integration
# =============================================================================

def test_api_analyze_request_not_found():
    """POST /api/requests/{id}/analyze returns 404 if request ID does not exist."""
    fake_id = uuid4()
    with patch("app.routers.ai.fetch_citizen_request", return_value=None):
        resp = client.post(f"/api/requests/{fake_id}/analyze")
        assert resp.status_code == 404


def test_api_analyze_request_unauthorized():
    """POST /api/requests/{id}/analyze returns 403 if requester does not own request."""
    req_id = uuid4()
    owner_id = uuid4()
    intruder_id = uuid4()

    mock_record = {
        "id": str(req_id),
        "user_id": str(owner_id),
        "description": "Clinic closed."
    }

    with patch("app.routers.ai.fetch_citizen_request", return_value=mock_record):
        resp = client.post(
            f"/api/requests/{req_id}/analyze?user_id={intruder_id}",
            headers={"X-User-Id": str(intruder_id)}
        )
        assert resp.status_code == 403


def test_api_analyze_request_success():
    """POST /api/requests/{id}/analyze runs analysis and returns structured response."""
    req_id = str(uuid4())
    user_id = str(uuid4())
    mock_record = {
        "id": req_id,
        "user_id": user_id,
        "description": "Hospital without electricity.",
        "category": "Healthcare"
    }

    mock_analysis_result = {
        "request_id": req_id,
        "prompt_version": "v1.0",
        "detected_language": "English",
        "translated_text": "Hospital without electricity.",
        "category": "Healthcare",
        "sub_category": "Hospital Power Supply",
        "urgency": "Critical",
        "summary": "Hospital operating without electrical power.",
        "keywords": ["hospital", "blackout", "generator"],
        "transcript": None,
        "image_analysis": {},
        "confidence": None,
        "processing_status": "completed",
        "error_message": None
    }

    with patch("app.routers.ai.fetch_citizen_request", return_value=mock_record), \
         patch("app.routers.ai.default_request_analyzer.analyze_citizen_request", return_value=mock_analysis_result), \
         patch("app.routers.ai.upsert_ai_analysis", return_value=mock_analysis_result):

        resp = client.post(
            f"/api/requests/{req_id}/analyze?user_id={user_id}",
            headers={"X-User-Id": user_id}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["request_id"] == req_id
        assert data["category"] == "Healthcare"
        assert data["urgency"] == "Critical"
        assert data["processing_status"] == "completed"


def test_api_get_request_analysis_endpoint():
    """GET /api/requests/{id}/analysis retrieves saved analysis."""
    req_id = str(uuid4())
    user_id = str(uuid4())
    mock_record = {
        "id": req_id,
        "user_id": user_id
    }
    mock_analysis = {
        "request_id": req_id,
        "prompt_version": "v1.0",
        "detected_language": "English",
        "translated_text": "Pothole filled with water",
        "category": "Roads",
        "sub_category": "Potholes",
        "urgency": "Medium",
        "summary": "Road pothole needing repair",
        "keywords": ["road", "pothole"],
        "confidence": None,
        "processing_status": "completed"
    }

    with patch("app.routers.ai.fetch_citizen_request", return_value=mock_record), \
         patch("app.routers.ai.fetch_ai_analysis", return_value=mock_analysis):

        resp = client.get(
            f"/api/requests/{req_id}/analysis?user_id={user_id}",
            headers={"X-User-Id": user_id}
        )
        assert resp.status_code == 200
        assert resp.json()["category"] == "Roads"


def test_api_direct_text_analysis():
    """POST /api/ai/analyze-text performs live text analysis."""
    mock_result = TextAnalysisResult(
        detected_language="English",
        translated_text="Severe water leakage on Main St.",
        category="Water",
        sub_category="Piped Water Supply",
        urgency="High",
        summary="Water pipe burst on main street.",
        keywords=["water", "pipe burst", "leakage"]
    )

    with patch("app.routers.ai.default_request_analyzer.analyze_text", return_value=mock_result):
        resp = client.post(
            "/api/ai/analyze-text",
            json={"text": "Severe water leakage on Main St."}
        )
        assert resp.status_code == 200
        assert resp.json()["category"] == "Water"
        assert resp.json()["urgency"] == "High"


# =============================================================================
# 8. Anti-Leakage & Safety Checks
# =============================================================================

def test_no_hardcoded_gemini_keys_in_code():
    """Verify no live AI keys are hardcoded in python or javascript files."""
    forbidden_pattern = "AI" + "za" + "Sy"
    this_file = Path(__file__).resolve()
    code_dirs = [
        Path(__file__).parent.parent,
        Path(__file__).parent.parent.parent / "frontend" / "src"
    ]
    for cdir in code_dirs:
        for fpath in cdir.rglob("*"):
            if fpath.resolve() == this_file:
                continue
            if fpath.suffix in (".py", ".js", ".jsx", ".ts", ".tsx", ".json") and "node_modules" not in str(fpath):
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                assert forbidden_pattern not in content, f"Possible hardcoded Google API Key found in {fpath}"
