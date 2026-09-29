import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """
    Verifies API root is functional and reports Phase 1 status.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "GFD Challenge DPI API"
    assert data["phase"] == "Phase 1 - Database + Storage Foundation"
    assert data["status"] == "online"


@patch("app.routers.health.check_db_health")
def test_health_endpoint_healthy(mock_check_db):
    """
    Verifies /health reports healthy status (HTTP 200) when database is reachable.
    """
    mock_check_db.return_value = {
        "connected": True,
        "provider": "postgresql",
        "message": "PostgreSQL reachable"
    }

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api"] == "running"
    assert data["database"] == "connected"
    assert "timestamp" in data
    # Ensure sensitive credentials are never leaked
    response_text = response.text.lower()
    assert "password" not in response_text
    assert "secret" not in response_text
    assert "service_role" not in response_text


@patch("app.routers.health.check_db_health")
def test_health_endpoint_degraded(mock_check_db):
    """
    Verifies /health reports degraded status (HTTP 503) when database is unreachable.
    """
    mock_check_db.return_value = {
        "connected": False,
        "provider": "postgresql",
        "message": "Database unreachable"
    }

    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["api"] == "running"
    assert data["database"] == "unreachable"
