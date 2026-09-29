"""
Automated tests for Administrative Endpoint Protection and Authorization.
Validates:
- Rejection of anonymous or unauthorized calls on admin endpoints in production
- Acceptance when valid X-Admin-Key is provided
- Acceptance when valid X-User-Role: admin is provided
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def test_admin_endpoint_requires_auth_in_production():
    """Verify that in production mode, anonymous access to /refresh and /process-pending is blocked."""
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "ADMIN_API_KEY", "super-secret-admin-token"):
        
        # Test 1: Anonymous call to refresh endpoint -> 403 Forbidden
        res_refresh = client.post("/api/infrastructure/refresh")
        assert res_refresh.status_code == 403
        assert "Forbidden" in res_refresh.json()["detail"]

        # Test 2: Anonymous call to batch process endpoint -> 403 Forbidden
        res_batch = client.post("/api/intelligence/process-pending")
        assert res_batch.status_code == 403
        assert "Forbidden" in res_batch.json()["detail"]


def test_admin_endpoint_accepts_valid_admin_key():
    """Verify that valid X-Admin-Key grants access."""
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "ADMIN_API_KEY", "super-secret-admin-token"):
        
        headers = {"X-Admin-Key": "super-secret-admin-token"}
        res_refresh = client.post("/api/infrastructure/refresh", headers=headers)
        assert res_refresh.status_code == 200
        assert res_refresh.json()["success"] is True


def test_admin_endpoint_accepts_admin_role_header():
    """Verify that X-User-Role: admin grants access."""
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "ADMIN_API_KEY", "super-secret-admin-token"):
        
        headers = {"X-User-Role": "admin"}
        res_refresh = client.post("/api/infrastructure/refresh", headers=headers)
        assert res_refresh.status_code == 200
        assert res_refresh.json()["success"] is True
