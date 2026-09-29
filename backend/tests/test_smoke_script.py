"""
Verifies smoke_test.py helper logic against FastAPI TestClient.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_smoke_endpoints_via_testclient():
    """Confirms all endpoints targeted by smoke_test.py respond correctly."""
    # 1. Root
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "GFD Challenge" in res_root.json()["service"]

    # 2. Health
    res_health = client.get("/health")
    assert res_health.status_code in [200, 503]
    assert res_health.json()["api"] == "running"

    # 3. Docs
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    # 4. District intelligence
    res_dist = client.get("/api/infrastructure/districts")
    assert res_dist.status_code == 200
    assert isinstance(res_dist.json(), list)

    # 5. Gap signals
    res_gap = client.get("/api/infrastructure/gap-signals")
    assert res_gap.status_code == 200
    assert isinstance(res_gap.json(), list)

    # 6. Clusters
    res_clusters = client.get("/api/intelligence/clusters")
    assert res_clusters.status_code == 200
    assert isinstance(res_clusters.json(), list)

    # 7. Emerging issues
    res_issues = client.get("/api/intelligence/emerging-issues")
    assert res_issues.status_code == 200
    assert isinstance(res_issues.json(), list)
