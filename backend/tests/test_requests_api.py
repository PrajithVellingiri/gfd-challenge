import uuid
from datetime import datetime
from unittest.mock import patch
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CitizenRequestCreate,
    CitizenRequestResponse,
    UrgencyLevel,
    RequestStatus,
    UserRole
)

client = TestClient(app)


def test_schema_valid_request():
    """
    Verifies valid CitizenRequestCreate schema instantiation.
    """
    req = CitizenRequestCreate(
        description="Broken water pipeline near the community center",
        category="water",
        language="en",
        latitude=12.9716,
        longitude=77.5946,
        location_name="Bangalore Central",
        urgency=UrgencyLevel.HIGH
    )
    assert req.category == "water"
    assert req.urgency == UrgencyLevel.HIGH
    assert req.latitude == 12.9716


def test_schema_invalid_coordinates():
    """
    Verifies coordinate boundary checks (latitude [-90, 90], longitude [-180, 180]).
    """
    with pytest.raises(ValidationError):
        CitizenRequestCreate(
            description="Invalid latitude test",
            category="roads",
            latitude=150.0,  # Invalid
            longitude=77.0
        )

    with pytest.raises(ValidationError):
        CitizenRequestCreate(
            description="Invalid longitude test",
            category="roads",
            latitude=12.0,
            longitude=-200.0  # Invalid
        )


def test_schema_role_enum():
    """
    Verifies UserRole enums.
    """
    assert UserRole.CITIZEN.value == "citizen"
    assert UserRole.POLICYMAKER.value == "policymaker"
    assert UserRole.ADMIN.value == "admin"


def test_create_request_rejects_unowned_storage_path():
    """
    Verifies that a user cannot submit a request pointing to another user's storage path.
    """
    user_id = uuid.uuid4()
    victim_user_id = uuid.uuid4()
    req_id = uuid.uuid4()

    # Image path belongs to victim_user_id, but user_id is the submitter
    payload = {
        "user_id": str(user_id),
        "description": "Suspicious reference",
        "category": "roads",
        "image_path": f"{victim_user_id}/{req_id}/secret.jpg"
    }

    response = client.post("/api/v1/requests", json=payload)
    assert response.status_code == 400
    assert "image_path does not conform" in response.json()["detail"]


@patch("app.routers.requests.insert_citizen_request")
def test_create_request_success(mock_insert):
    """
    Verifies successful citizen request creation flow.
    """
    req_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.utcnow()

    mock_insert.return_value = {
        "id": req_id,
        "user_id": user_id,
        "description": "Pothole on 5th cross main road",
        "category": "roads",
        "language": "en",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "location_name": "Chennai North",
        "urgency": "medium",
        "status": "submitted",
        "image_path": f"{user_id}/{req_id}/pothole.jpg",
        "audio_path": None,
        "extracted_intent": None,
        "ai_category": None,
        "ai_confidence": None,
        "extracted_entities": [],
        "ai_analysis": {},
        "cluster_id": None,
        "created_at": now,
        "updated_at": now
    }

    payload = {
        "user_id": str(user_id),
        "description": "Pothole on 5th cross main road",
        "category": "roads",
        "language": "en",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "location_name": "Chennai North",
        "urgency": "medium",
        "image_path": f"{user_id}/{req_id}/pothole.jpg"
    }

    response = client.post("/api/v1/requests", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(req_id)
    assert data["status"] == "submitted"
    assert data["category"] == "roads"


@patch("app.routers.requests.fetch_citizen_request")
def test_get_request_by_id(mock_fetch):
    """
    Verifies fetching citizen request by ID.
    """
    req_id = uuid.uuid4()
    now = datetime.utcnow()

    mock_fetch.return_value = {
        "id": req_id,
        "user_id": None,
        "description": "Broken streetlight",
        "category": "electricity",
        "language": "en",
        "latitude": None,
        "longitude": None,
        "location_name": None,
        "urgency": "low",
        "status": "submitted",
        "image_path": None,
        "audio_path": None,
        "extracted_intent": None,
        "ai_category": None,
        "ai_confidence": None,
        "extracted_entities": None,
        "ai_analysis": None,
        "cluster_id": None,
        "created_at": now,
        "updated_at": now
    }

    response = client.get(f"/api/v1/requests/{req_id}")
    assert response.status_code == 200
    assert response.json()["category"] == "electricity"


@patch("app.routers.requests.fetch_citizen_request")
def test_get_request_not_found(mock_fetch):
    """
    Verifies 404 response when request does not exist.
    """
    mock_fetch.return_value = None
    random_id = uuid.uuid4()
    response = client.get(f"/api/v1/requests/{random_id}")
    assert response.status_code == 404
