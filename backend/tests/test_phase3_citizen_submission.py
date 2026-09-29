import io
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import CitizenRequestCreate, UrgencyLevel

client = TestClient(app)


def test_phase3_valid_citizen_submission_with_district_resolution():
    """
    Tests full citizen submission workflow with automatic PostGIS/Shapely district resolution.
    Coordinates (12.9716, 77.5946) fall inside Bengaluru Urban.
    """
    user_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.utcnow()

    with patch("app.routers.requests.insert_citizen_request") as mock_insert:
        # Mock database insert returning the saved record
        mock_insert.side_effect = lambda data: {
            "id": req_id,
            "user_id": data.get("user_id"),
            "district_id": data.get("district_id"),
            "category": data.get("category"),
            "description": data.get("description"),
            "status": "submitted",
            "created_at": now,
            "updated_at": now
        }

        payload = {
            "user_id": str(user_id),
            "description": "Primary healthcare centre lacks anti-venom and emergency oxygen cylinders.",
            "category": "Healthcare",
            "language": "English",
            "urgency": "High",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "location_name": "Koramangala Community Centre"
        }

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["request_id"] == str(req_id)
        assert data["status"] == "submitted"
        assert data["district_name"] == "Bengaluru Urban"
        assert data["district_id"] is not None


def test_phase3_submission_outside_district_boundaries():
    """
    Verifies that coordinates outside known district boundaries preserve coordinates
    without assigning an incorrect district.
    """
    user_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.utcnow()

    with patch("app.routers.requests.insert_citizen_request") as mock_insert:
        mock_insert.side_effect = lambda data: {
            "id": req_id,
            "user_id": data.get("user_id"),
            "district_id": data.get("district_id"),
            "category": data.get("category"),
            "status": "submitted",
            "created_at": now,
            "updated_at": now
        }

        # Point in middle of the Indian Ocean (lat 0.0, lon 80.0)
        payload = {
            "user_id": str(user_id),
            "description": "Maritime communication satellite tower signal defect.",
            "category": "digital infrastructure",
            "latitude": 0.0,
            "longitude": 80.0,
            "location_name": "Offshore Station"
        }

        response = client.post("/api/requests", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["district_id"] is None
        assert data["district_name"] is None


def test_phase3_validation_rejections():
    """
    Verifies frontend/backend validation rules: description length, invalid urgency, invalid coordinates.
    """
    # 1. Description too short (< 5 chars)
    res = client.post("/api/requests", json={
        "description": "bad",
        "category": "roads",
        "location_name": "Main Street"
    })
    assert res.status_code == 422

    # 2. Invalid coordinates bounds (lat > 90)
    res = client.post("/api/requests", json={
        "description": "Pothole on 4th street",
        "category": "roads",
        "latitude": 150.0,
        "longitude": 77.0
    })
    assert res.status_code == 422

    # 3. Invalid urgency level
    res = client.post("/api/requests", json={
        "description": "Dangerous culvert collapse",
        "category": "roads",
        "urgency": "extreme_super_urgent",
        "location_name": "Valley Road"
    })
    assert res.status_code == 422


def test_phase3_cross_user_storage_path_rejection():
    """
    Ensures a citizen cannot attach media belonging to another user's storage directory.
    """
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    req_id = uuid.uuid4()

    payload = {
        "user_id": str(user_a),
        "description": "Unauthorized access attempt to user B media",
        "category": "water",
        "location_name": "Town Square",
        "image_path": f"{user_b}/{req_id}/private_photo.jpg"
    }

    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400
    assert "image_path does not conform" in response.json()["detail"]


def test_phase3_file_upload_validations():
    """
    Verifies file upload endpoint validates MIME types and file size boundaries.
    """
    user_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    # 1. Invalid MIME type for image
    bad_file = io.BytesIO(b"#!/bin/bash\necho dangerous")
    response = client.post(
        "/api/requests/upload",
        data={"user_id": user_id, "request_id": req_id, "bucket_type": "image"},
        files={"file": ("malicious.sh", bad_file, "application/x-sh")}
    )
    assert response.status_code == 400
    assert "Invalid file MIME type" in response.json()["detail"]

    # 2. Valid image upload within 10MB
    valid_png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)
    response = client.post(
        "/api/requests/upload",
        data={"user_id": user_id, "request_id": req_id, "bucket_type": "image"},
        files={"file": ("pothole.png", valid_png, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["bucket"] == "citizen-images"
    assert data["storage_path"] == f"{user_id}/{req_id}/pothole.png"

    # 3. Oversized image (> 10MB)
    huge_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    huge_file = io.BytesIO(huge_bytes)
    response = client.post(
        "/api/requests/upload",
        data={"user_id": user_id, "request_id": req_id, "bucket_type": "image"},
        files={"file": ("huge.jpg", huge_file, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "exceeds maximum allowed size" in response.json()["detail"]

    # 4. Valid audio upload within 25MB
    valid_audio = io.BytesIO(b"ID3" + b"\x00" * 2048)
    response = client.post(
        "/api/requests/upload",
        data={"user_id": user_id, "request_id": req_id, "bucket_type": "audio"},
        files={"file": ("voice_note.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["bucket"] == "citizen-audio"
    assert data["storage_path"] == f"{user_id}/{req_id}/voice_note.mp3"


def test_phase3_request_retrieval_authorization():
    """
    Verifies that a citizen cannot view another citizen's private request.
    """
    owner_id = uuid.uuid4()
    other_citizen_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.utcnow()

    with patch("app.routers.requests.fetch_citizen_request") as mock_fetch:
        mock_fetch.return_value = {
            "id": req_id,
            "user_id": owner_id,
            "description": "Private sensitive drainage grievance",
            "category": "water",
            "language": "en",
            "urgency": "medium",
            "status": "submitted",
            "created_at": now,
            "updated_at": now
        }

        # 1. Owner can access
        resp_owner = client.get(f"/api/requests/{req_id}?user_id={owner_id}")
        assert resp_owner.status_code == 200

        # 2. Unauthorized citizen blocked with 403 Forbidden
        resp_other = client.get(f"/api/requests/{req_id}?user_id={other_citizen_id}")
        assert resp_other.status_code == 403
        assert "Unauthorized" in resp_other.json()["detail"]


def test_phase3_complete_workflow_integration():
    """
    Integration test:
    1. Authenticated citizen creates request with coordinates and media reference.
    2. District is resolved via spatial lookup (e.g. Chennai).
    3. Record is stored and returned with request_id.
    4. Citizen retrieves own request history.
    """
    citizen_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.utcnow()

    stored_records = []

    def fake_insert(data):
        rec = {
            "id": req_id,
            "user_id": citizen_id,
            "district_id": data.get("district_id"),
            "description": data["description"],
            "category": data["category"],
            "language": data.get("language", "en"),
            "urgency": data.get("urgency", "medium"),
            "status": "submitted",
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "location_name": data.get("location_name"),
            "image_path": data.get("image_path"),
            "audio_path": data.get("audio_path"),
            "created_at": now,
            "updated_at": now
        }
        stored_records.append(rec)
        return rec

    def fake_list(user_id=None, limit=50, offset=0):
        return [r for r in stored_records if str(r["user_id"]) == str(user_id)]

    with patch("app.routers.requests.insert_citizen_request", side_effect=fake_insert), \
         patch("app.routers.requests.list_citizen_requests", side_effect=fake_list):

        # Step 1: Submit request (Chennai coordinates: 13.0827, 80.2707)
        submission_payload = {
            "user_id": str(citizen_id),
            "description": "Piped drinking water supply is discolored and smells like sewage.",
            "category": "water",
            "language": "ta",
            "urgency": "critical",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "location_name": "Royapettah Ward 112",
            "image_path": f"{citizen_id}/{req_id}/water_sample.jpg",
            "audio_path": f"{citizen_id}/{req_id}/voice_complaint.mp3"
        }

        submit_resp = client.post("/api/requests", json=submission_payload)
        assert submit_resp.status_code == 201
        res_data = submit_resp.json()
        assert res_data["success"] is True
        assert res_data["request_id"] == str(req_id)
        assert res_data["district_name"] == "Chennai"

        # Step 2: Fetch citizen request history
        history_resp = client.get(f"/api/requests?user_id={citizen_id}")
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        assert len(history_data) == 1
        item = history_data[0]
        assert item["id"] == str(req_id)
        assert item["category"] == "water"
        assert item["urgency"] == "critical"
        assert item["image_path"] == f"{citizen_id}/{req_id}/water_sample.jpg"
        assert item["audio_path"] == f"{citizen_id}/{req_id}/voice_complaint.mp3"
