"""
Automated Test Suite for Phase 5: Request Intelligence.
Validates:
- Migration 006 schema for request_embeddings, request_similarities, clusters, and emerging_issues
- 768-dim semantic embedding generation and deterministic mock behavior
- Cosine similarity and nearest neighbor search
- Duplicate vs Similar classification with geographic location awareness
- District-aware and category-aware semantic clustering using DBSCAN
- Deterministic cluster label synthesis
- Emerging issue surge detection with period-over-period growth indicators
- FastAPI intelligence endpoints authorization, retrieval, and privacy guarantees
- Anti-leakage and personal identifier isolation
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.intelligence.embeddings import (
    MockEmbeddingProvider,
    extract_request_text_for_embedding,
    get_embedding_provider,
)
from app.services.intelligence.similarity import (
    cosine_similarity,
    cosine_distance,
    rank_nearest_neighbors,
)
from app.services.intelligence.duplicate_detector import (
    calculate_haversine_distance_km,
    are_locations_coincident,
    classify_relationship,
    find_duplicates_for_request,
)
from app.services.intelligence.clustering import (
    RequestClusterer,
    synthesize_cluster_label,
)
from app.services.intelligence.emerging_issues import (
    EmergingIssueDetector,
    parse_timestamp,
)
from app.services.intelligence.intelligence_service import (
    IntelligenceService,
    default_intelligence_service,
)

client = TestClient(app)
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


# =============================================================================
# 1. Migration 006 Schema Verification
# =============================================================================

def test_migration_006_sql_schema():
    """Verify migration 006 creates all required intelligence tables and indexes."""
    migration_file = MIGRATIONS_DIR / "006_request_intelligence.sql"
    assert migration_file.exists(), "Migration 006 file is missing!"

    sql = migration_file.read_text(encoding="utf-8").lower()
    required_tables = [
        "public.request_embeddings",
        "public.request_similarities",
        "public.request_clusters",
        "public.cluster_memberships",
        "public.emerging_issues",
    ]
    for tbl in required_tables:
        assert f"create table if not exists {tbl}" in sql, f"Missing table {tbl}"

    # Verify vector(768)
    assert "vector(768)" in sql
    # Verify relationship_type check constraint
    assert "'similar'" in sql and "'duplicate'" in sql and "'related'" in sql
    # Verify RLS enablement
    assert "enable row level security" in sql


# =============================================================================
# 2. Semantic Embedding Generation
# =============================================================================

def test_mock_embedding_dimensions_and_determinism():
    """Verify MockEmbeddingProvider generates exact 768-dim normalized vectors deterministically."""
    provider = MockEmbeddingProvider(dimension=768)

    text_a = "Our village drinking water pipeline is damaged."
    text_b = "Our village drinking water pipeline is damaged."
    text_c = "Primary Health Centre needs emergency doctors."

    vec_a = provider.embed_text(text_a)
    vec_b = provider.embed_text(text_b)
    vec_c = provider.embed_text(text_c)

    assert len(vec_a) == 768
    assert len(vec_b) == 768
    assert len(vec_c) == 768

    # Determinism: Identical text produces identical vector
    assert vec_a == vec_b
    assert cosine_similarity(vec_a, vec_b) == pytest.approx(1.0, abs=1e-5)

    # Different domains produce different vectors
    sim_ac = cosine_similarity(vec_a, vec_c)
    assert sim_ac < 0.95


def test_extract_request_text_prioritization():
    """Verify extraction prioritizes English translation/summary over raw description."""
    req = {"description": "Raw untranslated regional grievance."}
    analysis = {
        "translated_text": "Drinking water pipeline leakage.",
        "category": "Water",
        "sub_category": "Piped Supply",
        "keywords": ["water", "pipeline"]
    }
    extracted = extract_request_text_for_embedding(req, analysis)
    assert "Drinking water pipeline leakage" in extracted
    assert "Category: Water" in extracted
    assert "Sub-category: Piped Supply" in extracted


# =============================================================================
# 3. Vector Similarity & Nearest Neighbors
# =============================================================================

def test_cosine_similarity_math():
    """Verify cosine similarity mathematical bounds and corner cases."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    v4 = [-1.0, 0.0, 0.0]
    v_zero = [0.0, 0.0, 0.0]

    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)
    assert cosine_similarity(v1, v4) == pytest.approx(-1.0)
    assert cosine_similarity(v1, v_zero) == 0.0
    assert cosine_distance(v1, v2) == pytest.approx(0.0)
    assert cosine_distance(v1, v4) == pytest.approx(2.0)


def test_rank_nearest_neighbors():
    """Verify candidate ranking respects similarity thresholds and excludes query ID."""
    q_vec = [1.0, 0.0, 0.0]
    candidates = [
        {"request_id": "req-self", "embedding": [1.0, 0.0, 0.0], "category": "Water"},
        {"request_id": "req-high", "embedding": [0.95, 0.31, 0.0], "category": "Water"},
        {"request_id": "req-med", "embedding": [0.75, 0.66, 0.0], "category": "Water"},
        {"request_id": "req-low", "embedding": [0.20, 0.97, 0.0], "category": "Roads"},
    ]

    ranked = rank_nearest_neighbors(
        query_vector=q_vec,
        candidate_records=candidates,
        top_k=5,
        min_threshold=0.70,
        exclude_request_id="req-self"
    )

    # req-self excluded, req-low filtered out (< 0.70)
    assert len(ranked) == 2
    assert ranked[0]["request_id"] == "req-high"
    assert ranked[1]["request_id"] == "req-med"
    assert ranked[0]["similarity_score"] > ranked[1]["similarity_score"]


# =============================================================================
# 4. Duplicate vs Similar with Location Awareness
# =============================================================================

def test_haversine_distance_calculation():
    """Verify coordinate distance calculation."""
    # Bangalore (12.9716, 77.5946) to Whitefield (12.9698, 77.7500) ~16.8 km
    d = calculate_haversine_distance_km(12.9716, 77.5946, 12.9698, 77.7500)
    assert 15.0 < d < 20.0


def test_duplicate_vs_similar_preserves_distinction():
    """
    CRITICAL REQUIREMENT (Section 10):
    Two requests can be semantically identical, but if they are from different
    districts, they must be classified as 'similar', NOT 'duplicate'.
    """
    dist_a = str(uuid4())
    dist_b = str(uuid4())

    req_village_x = {
        "id": "req-1",
        "district_id": dist_a,
        "description": "Village X needs a drinking water pipeline."
    }
    req_village_y = {
        "id": "req-2",
        "district_id": dist_b,
        "description": "Village Y needs a drinking water pipeline."
    }
    req_village_x_repeat = {
        "id": "req-3",
        "district_id": dist_a,
        "description": "Drinking water pipeline needed in Village X."
    }

    # Same district + high similarity -> duplicate
    rel_dup, reason_dup = classify_relationship(
        req_village_x,
        req_village_x_repeat,
        similarity_score=0.94,
        duplicate_threshold=0.90
    )
    assert rel_dup == "duplicate"
    assert "coincident geography" in reason_dup

    # Different district + high similarity -> similar (NEVER duplicate)
    rel_diff_dist, reason_diff = classify_relationship(
        req_village_x,
        req_village_y,
        similarity_score=0.94,
        duplicate_threshold=0.90
    )
    assert rel_diff_dist == "similar"
    assert "separated geography" in reason_diff


# =============================================================================
# 5. Semantic Clustering (DBSCAN + District/Category Awareness)
# =============================================================================

def test_synthesize_cluster_label():
    """Verify cluster label synthesis extracts top sub-category or keyword deterministically."""
    members = [
        {"sub_category": "Hospital Access", "summary": "Clinic lacks doctor."},
        {"sub_category": "Hospital Access", "summary": "No staff at primary clinic."},
        {"sub_category": "Ambulance Shortage", "summary": "Ambulance unavailable."}
    ]
    label, summary = synthesize_cluster_label("Healthcare", members)
    assert label == "Hospital Access"
    assert "Cluster of 3" in summary


def test_district_aware_semantic_clustering():
    """
    Verify requests are clustered within (district, category) boundaries
    and distinct districts are NOT merged into a single cluster.
    """
    dist_1 = str(uuid4())
    dist_2 = str(uuid4())

    prov = MockEmbeddingProvider(dimension=768)
    vec_water = prov.embed_text("Drinking water supply shortage in rural ward.")

    records = [
        # District 1 Water Group
        {"request_id": "r1", "district_id": dist_1, "category": "Water", "sub_category": "Piped Supply", "embedding": vec_water},
        {"request_id": "r2", "district_id": dist_1, "category": "Water", "sub_category": "Piped Supply", "embedding": vec_water},
        # District 2 Water Group
        {"request_id": "r3", "district_id": dist_2, "category": "Water", "sub_category": "Piped Supply", "embedding": vec_water},
        {"request_id": "r4", "district_id": dist_2, "category": "Water", "sub_category": "Piped Supply", "embedding": vec_water},
    ]

    clusterer = RequestClusterer(eps=0.35, min_samples=2)
    clusters = clusterer.cluster_requests(records)

    # Must produce 2 separate clusters for the two separate districts
    assert len(clusters) == 2
    districts_in_clusters = {c["district_id"] for c in clusters}
    assert dist_1 in districts_in_clusters
    assert dist_2 in districts_in_clusters


# =============================================================================
# 6. Emerging Issue Detection
# =============================================================================

def test_emerging_issues_surge_and_growth_calc():
    """Verify period-over-period growth calculation and new surge indicator."""
    detector = EmergingIssueDetector(window_days=7, min_current_threshold=3)
    now = datetime.now(timezone.utc)

    # 4 requests in current 7 days, 1 in previous 7 days -> 300% growth
    requests = [
        {"district_id": "dist-1", "category": "Water", "sub_category": "Contamination", "created_at": (now - timedelta(days=2)).isoformat()},
        {"district_id": "dist-1", "category": "Water", "sub_category": "Contamination", "created_at": (now - timedelta(days=3)).isoformat()},
        {"district_id": "dist-1", "category": "Water", "sub_category": "Contamination", "created_at": (now - timedelta(days=4)).isoformat()},
        {"district_id": "dist-1", "category": "Water", "sub_category": "Contamination", "created_at": (now - timedelta(days=5)).isoformat()},
        {"district_id": "dist-1", "category": "Water", "sub_category": "Contamination", "created_at": (now - timedelta(days=10)).isoformat()},
    ]

    issues = detector.detect_emerging_issues(requests, reference_time=now)
    assert len(issues) == 1
    iss = issues[0]
    assert iss["current_count"] == 4
    assert iss["previous_count"] == 1
    assert iss["growth_percentage"] == 300.0
    assert iss["indicator"] == "increasing"


def test_emerging_issues_zero_previous_count():
    """
    CRITICAL REQUIREMENT (Section 15):
    If previous count is zero, growth_percentage must be None (null), NOT 100% or infinity.
    """
    detector = EmergingIssueDetector(window_days=7, min_current_threshold=3)
    now = datetime.now(timezone.utc)

    # 3 requests in current 7 days, 0 in previous 7 days
    requests = [
        {"district_id": "dist-1", "category": "Roads", "sub_category": "Bridge Damage", "created_at": (now - timedelta(days=1)).isoformat()},
        {"district_id": "dist-1", "category": "Roads", "sub_category": "Bridge Damage", "created_at": (now - timedelta(days=2)).isoformat()},
        {"district_id": "dist-1", "category": "Roads", "sub_category": "Bridge Damage", "created_at": (now - timedelta(days=3)).isoformat()},
    ]

    issues = detector.detect_emerging_issues(requests, reference_time=now)
    assert len(issues) == 1
    iss = issues[0]
    assert iss["current_count"] == 3
    assert iss["previous_count"] == 0
    assert iss["growth_percentage"] is None
    assert iss["indicator"] == "new"


# =============================================================================
# 7. FastAPI Intelligence Endpoints Integration
# =============================================================================

def test_api_similar_requests_not_found():
    """GET /api/requests/{id}/similar returns 404 for unknown request."""
    fake_id = uuid4()
    with patch("app.routers.intelligence.fetch_citizen_request", return_value=None):
        resp = client.get(f"/api/requests/{fake_id}/similar")
        assert resp.status_code == 404


def test_api_similar_requests_unauthorized():
    """GET /api/requests/{id}/similar returns 403 if requester does not own request."""
    req_id = uuid4()
    owner_id = uuid4()
    intruder_id = uuid4()
    mock_record = {"id": str(req_id), "user_id": str(owner_id)}

    with patch("app.routers.intelligence.fetch_citizen_request", return_value=mock_record):
        resp = client.get(
            f"/api/requests/{req_id}/similar?user_id={intruder_id}",
            headers={"X-User-Id": str(intruder_id)}
        )
        assert resp.status_code == 403


def test_api_similar_requests_success_anonymized():
    """GET /api/requests/{id}/similar returns anonymized matches without personal data."""
    req_id = str(uuid4())
    user_id = str(uuid4())
    mock_record = {"id": req_id, "user_id": user_id, "category": "Water"}

    mock_sims = [
        {
            "request_id": str(uuid4()),
            "similarity_score": 0.88,
            "category": "Water",
            "sub_category": "Pipeline",
            "district_id": str(uuid4()),
            "relationship_type": "similar",
            "explanation": "High similarity in water category.",
            "created_at": "2026-09-29T10:00:00Z"
        }
    ]

    with patch("app.routers.intelligence.fetch_citizen_request", return_value=mock_record), \
         patch.object(default_intelligence_service, "find_similar_requests", return_value=mock_sims):

        resp = client.get(
            f"/api/requests/{req_id}/similar?user_id={user_id}",
            headers={"X-User-Id": user_id}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        item = data[0]
        assert item["similarity_score"] == 0.88
        assert item["relationship_type"] == "similar"
        # Privacy guarantee: personal data must not be in the response
        assert "name" not in item
        assert "email" not in item
        assert "phone" not in item
        assert "description" not in item


def test_api_duplicates_endpoint():
    """GET /api/requests/{id}/duplicates returns verified duplicate groups."""
    req_id = str(uuid4())
    user_id = str(uuid4())
    mock_record = {"id": req_id, "user_id": user_id}

    mock_dups = [
        {
            "request_id": str(uuid4()),
            "similarity_score": 0.95,
            "category": "Healthcare",
            "sub_category": "PHC Doctor",
            "district_id": str(uuid4()),
            "relationship_type": "duplicate",
            "explanation": "High semantic similarity (0.95) and coincident geography.",
            "created_at": "2026-09-29T10:00:00Z"
        }
    ]

    with patch("app.routers.intelligence.fetch_citizen_request", return_value=mock_record), \
         patch.object(default_intelligence_service, "detect_duplicates", return_value=mock_dups):

        resp = client.get(
            f"/api/requests/{req_id}/duplicates?user_id={user_id}",
            headers={"X-User-Id": user_id}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["relationship_type"] == "duplicate"


def test_api_clusters_and_emerging_issues_endpoints():
    """Verify cluster and emerging issue discovery endpoints."""
    mock_clusters = [
        {
            "id": str(uuid4()),
            "cluster_label": "Rural Hospital Access",
            "category": "Healthcare",
            "district_id": str(uuid4()),
            "request_count": 47,
            "summary": "Cluster of 47 requests regarding PHC doctor shortages."
        }
    ]
    mock_issues = [
        {
            "id": str(uuid4()),
            "title": "Increasing drinking water requests (+287%)",
            "description": "31 requests in current window vs 8 in previous window.",
            "category": "Water",
            "sub_category": "Pipeline",
            "district_id": str(uuid4()),
            "current_count": 31,
            "previous_count": 8,
            "growth_percentage": 287.5,
            "indicator": "increasing",
            "signal_type": "AI/data-derived signal (advisory governance triage)"
        }
    ]

    with patch("app.routers.intelligence.fetch_clusters", return_value=mock_clusters), \
         patch.object(default_intelligence_service, "detect_emerging_issues", return_value=mock_issues):

        resp_clusters = client.get("/api/intelligence/clusters")
        assert resp_clusters.status_code == 200
        assert resp_clusters.json()[0]["cluster_label"] == "Rural Hospital Access"

        resp_issues = client.get("/api/intelligence/emerging-issues")
        assert resp_issues.status_code == 200
        assert resp_issues.json()[0]["growth_percentage"] == 287.5
        assert resp_issues.json()[0]["indicator"] == "increasing"


def test_api_batch_processing_endpoint():
    """POST /api/intelligence/process-pending batch processes records."""
    mock_result = {
        "success": True,
        "embeddings_generated": 15,
        "similarities_recorded": 32,
        "clusters_count": 4,
        "emerging_issues_count": 2
    }
    with patch.object(default_intelligence_service, "process_pending_intelligence", return_value=mock_result):
        resp = client.post("/api/intelligence/process-pending?batch_size=20")
        assert resp.status_code == 200
        assert resp.json()["embeddings_generated"] == 15
        assert resp.json()["clusters_count"] == 4
