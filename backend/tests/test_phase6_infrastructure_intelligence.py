"""
Automated Test Suite for Phase 6: Infrastructure Intelligence & Gap Detection.
Validates:
- Migration 007 schema: district_intelligence table, indexes, RLS policies
- Population normalization and zero/missing divisor safety
- Cross-district relative percentile ranking calculations
- Healthcare, investment, and health indicator metric aggregations
- Demand metrics, growth, and per-capita normalization
- Explainable Gap Signal rules (potential_gap, infrastructure_pressure, balanced, insufficient_data)
- Data provenance tracking (Census 2011 baseline, HMIS, NFHS-5, synthetic flags)
- FastAPI endpoints for district intelligence, sectors, gap signals, and refresh
- Privacy guarantees: zero PII leakage in aggregate intelligence outputs
"""

import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.infrastructure.metrics import (
    calculate_population_ratio,
    calculate_percentile_rank,
    aggregate_healthcare_infrastructure,
    aggregate_district_investments,
    aggregate_health_indicators,
)
from app.services.infrastructure.demand_metrics import calculate_district_demand_metrics
from app.services.infrastructure.gap_detector import GapSignalDetector
from app.services.infrastructure.district_intelligence import DistrictIntelligenceAssembler
from app.services.infrastructure.infrastructure_service import (
    InfrastructureIntelligenceService,
    default_infrastructure_service,
)
from app.db import (
    save_district_intelligence_records,
    fetch_district_intelligence,
    list_district_intelligence_records,
)

client = TestClient(app)
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


# =============================================================================
# 1. Migration 007 Schema Verification
# =============================================================================

def test_migration_007_schema():
    """Verify that 007_infrastructure_intelligence.sql contains all necessary fields and constraints."""
    migration_file = MIGRATIONS_DIR / "007_infrastructure_intelligence.sql"
    assert migration_file.exists(), "007_infrastructure_intelligence.sql not found"
    sql = migration_file.read_text(encoding="utf-8").lower()

    assert "create table if not exists public.district_intelligence" in sql
    assert "district_id uuid not null" in sql
    assert "sector varchar(100) not null" in sql
    assert "population bigint" in sql
    assert "demand_percentile numeric(5, 2)" in sql
    assert "infrastructure_percentile numeric(5, 2)" in sql
    assert "mismatch_signal varchar(100)" in sql
    assert "gap_signal jsonb" in sql
    assert "data_sources jsonb" in sql
    assert "uq_district_intelligence_district_sector" in sql
    assert "enable row level security" in sql


# =============================================================================
# 2. Population Normalization & Zero-Divisor Safety
# =============================================================================

def test_population_ratio_calculation():
    """Test population ratio calculation with standard values."""
    # 50 facilities in 1,000,000 population -> 5.0 per 100k
    ratio = calculate_population_ratio(50, 1000000, multiplier=100000.0)
    assert ratio == 5.0

    # 15 requests in 500,000 population -> 0.3 per 10k
    req_ratio = calculate_population_ratio(15, 500000, multiplier=10000.0)
    assert req_ratio == 0.3


def test_population_ratio_zero_and_none_safety():
    """Ensure zero, negative, or None population safely returns None without exception."""
    assert calculate_population_ratio(10, 0) is None
    assert calculate_population_ratio(10, -5000) is None
    assert calculate_population_ratio(10, None) is None
    assert calculate_population_ratio(None, 100000) is None


# =============================================================================
# 3. Cross-District Relative Percentile Ranking
# =============================================================================

def test_percentile_rank_higher_is_better():
    """Test standard percentile ranking where higher values receive higher percentiles."""
    values_by_id = {
        "d1": 10.0,
        "d2": 20.0,
        "d3": 30.0,
        "d4": 40.0,
        "d5": 50.0
    }
    pcts, available = calculate_percentile_rank(values_by_id, higher_is_better=True)
    assert available is True
    # 5 entities, sorted: [10, 20, 30, 40, 50]
    # d3 (30.0): 3 values <= 30 -> 3/5 = 60.0%
    assert pcts["d3"] == 60.0
    # d5 (50.0): 5/5 = 100.0%
    assert pcts["d5"] == 100.0
    # d1 (10.0): 1/5 = 20.0%
    assert pcts["d1"] == 20.0


def test_percentile_rank_lower_is_better():
    """Test inverted ranking where lower values receive higher percentiles."""
    values_by_id = {
        "d1": 10.0,
        "d2": 20.0,
        "d3": 30.0,
        "d4": 40.0,
        "d5": 50.0
    }
    pcts, available = calculate_percentile_rank(values_by_id, higher_is_better=False)
    assert available is True
    # Inverted: 100.0 - 20.0 = 80.0%
    assert pcts["d1"] == 80.0


def test_percentile_rank_insufficient_sample():
    """When sample size is under 3 or target value is None, benchmark is unavailable."""
    small_sample = {"d1": 10.0, "d2": 20.0}
    pcts, available = calculate_percentile_rank(small_sample)
    assert available is False
    assert pcts["d1"] is None
    assert pcts["d2"] is None


# =============================================================================
# 4. Metric Aggregations (Healthcare, Investments, Health Indicators)
# =============================================================================

def test_aggregate_healthcare_infrastructure():
    """Verify aggregation of health facilities, doctors, and beds per capita."""
    facilities = [
        {"capacity_value": {"facility_type": "District Hospital", "bed_count": 30, "doctor_count": 8}},
        {"capacity_value": {"facility_type": "Primary Health Centre", "bed_count": 6, "doctor_count": 2}},
        {"capacity_value": {"facility_type": "Sub Centre", "bed_count": 0, "doctor_count": 0}},
    ]
    population = 200000

    metrics = aggregate_healthcare_infrastructure(facilities, population)
    assert metrics["data_available"] is True
    assert metrics["facility_count"] == 3
    assert metrics["hospital_count"] == 1
    assert metrics["total_beds"] == 36
    assert metrics["doctor_count"] == 10
    # 36 beds / 200,000 * 10,000 = 1.8
    assert metrics["beds_per_10000"] == 1.8
    # 10 doctors / 200,000 * 10,000 = 0.5
    assert metrics["doctors_per_10000"] == 0.5


def test_aggregate_district_investments():
    """Verify investment project counts and budget sums."""
    investments = [
        {"category": "healthcare", "amount": 50000000.0, "financial_year": "2023-24", "is_synthetic": True},
        {"category": "healthcare", "amount": 30000000.0, "financial_year": "2024-25", "is_synthetic": True},
        {"category": "education", "amount": 10000000.0, "financial_year": "2023-24", "is_synthetic": True},
    ]
    population = 1000000

    invest_data = aggregate_district_investments(investments, population)
    assert invest_data["data_available"] is True
    assert invest_data["total_investment"] == 90000000.0
    assert invest_data["investment_per_capita"] == 90.0
    assert invest_data["by_sector"]["healthcare"] == 80000000.0
    assert invest_data["by_sector"]["education"] == 10000000.0
    assert invest_data["is_synthetic"] is True


def test_aggregate_health_indicators():
    """Verify extraction of NFHS-5 indicator values."""
    indicators = [
        {"indicator_name": "NFHS5_INST_BIRTHS", "indicator_value": 94.5},
        {"indicator_name": "NFHS5_IMMUNIZATION", "indicator_value": 88.0},
        {"indicator_name": "NFHS5_STUNTING", "indicator_value": 22.3},
    ]

    res = aggregate_health_indicators(indicators)
    assert res["data_available"] is True
    assert res["indicators"]["NFHS5_INST_BIRTHS"] == 94.5
    assert res["indicators"]["NFHS5_IMMUNIZATION"] == 88.0
    assert res["indicators"]["NFHS5_STUNTING"] == 22.3
    assert "NFHS-5" in res["survey_round"]


# =============================================================================
# 5. Demand Metrics Calculation
# =============================================================================

def test_calculate_district_demand_metrics():
    """Verify citizen request aggregation, recent window counts, growth, and per 10k rates."""
    now = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
    requests = [
        {"created_at": (now - timedelta(days=2)).isoformat(), "category": "healthcare"},
        {"created_at": (now - timedelta(days=4)).isoformat(), "category": "healthcare"},
        {"created_at": (now - timedelta(days=10)).isoformat(), "category": "healthcare"},
        {"created_at": (now - timedelta(days=20)).isoformat(), "category": "water"},
    ]
    population = 100000

    metrics = calculate_district_demand_metrics(requests, population, reference_time=now)
    assert metrics["total_requests"] == 4
    assert metrics["requests_last_7_days"] == 2
    assert metrics["requests_previous_7_days"] == 1
    # 2 vs 1 -> +100% growth
    assert metrics["request_growth_percentage"] == 100.0
    # 4 requests in 100k -> 0.4 per 10k
    assert metrics["requests_per_10000"] == 0.4
    assert metrics["requests_by_sector"]["healthcare"] == 3
    assert metrics["requests_by_sector"]["water"] == 1


# =============================================================================
# 6. Explainable Gap Signal Rules
# =============================================================================

def test_gap_signal_high_demand_low_infrastructure():
    """Potential gap signal when citizen demand is high and infrastructure percentile is low."""
    detector = GapSignalDetector()
    signal = detector.evaluate_sector_gap_signal(
        sector="healthcare",
        demand_percentile=85.0,
        infrastructure_percentile=20.0,
        demand_metrics={"total_requests": 50, "requests_per_10000": 3.2},
        infrastructure_metrics={"data_available": True, "hospital_count": 1, "total_beds": 20, "beds_per_10000": 0.4}
    )

    assert signal["signal_type"] == "potential_gap"
    assert signal["severity"] == "high"
    assert signal["mismatch_state"] == "high_demand_low_infrastructure"
    assert "85th percentile" in signal["summary"]
    assert "20th percentile" in signal["summary"]
    assert "evidence" in signal
    assert "what_was_observed" in signal["evidence"]
    assert "infrastructure_observed" in signal["evidence"]


def test_gap_signal_infrastructure_pressure():
    """Infrastructure pressure when demand is high and infrastructure is near average."""
    detector = GapSignalDetector()
    signal = detector.evaluate_sector_gap_signal(
        sector="healthcare",
        demand_percentile=78.0,
        infrastructure_percentile=45.0,
        demand_metrics={"total_requests": 30, "requests_per_10000": 1.5},
        infrastructure_metrics={"data_available": True, "hospital_count": 3, "total_beds": 80, "beds_per_10000": 1.2}
    )

    assert signal["signal_type"] == "infrastructure_pressure"
    assert signal["severity"] == "medium"
    assert signal["mismatch_state"] == "high_demand_moderate_infrastructure"


def test_gap_signal_demand_supply_signal():
    """Demand-supply signal when cluster concentration is significant."""
    detector = GapSignalDetector()
    signal = detector.evaluate_sector_gap_signal(
        sector="healthcare",
        demand_percentile=55.0,
        infrastructure_percentile=50.0,
        demand_metrics={"total_requests": 20, "requests_per_10000": 1.0},
        infrastructure_metrics={"data_available": True, "hospital_count": 2, "total_beds": 50},
        cluster_metrics={"top_cluster": "Emergency Ward Shortage", "top_cluster_percentage": 65.0}
    )

    assert signal["signal_type"] == "demand_supply_signal"
    assert signal["mismatch_state"] == "concentrated_cluster_demand"


def test_gap_signal_balanced():
    """Balanced signal when demand and infrastructure percentiles are within normal ranges."""
    detector = GapSignalDetector()
    signal = detector.evaluate_sector_gap_signal(
        sector="healthcare",
        demand_percentile=50.0,
        infrastructure_percentile=55.0,
        demand_metrics={"total_requests": 15, "requests_per_10000": 0.8},
        infrastructure_metrics={"data_available": True, "hospital_count": 2, "total_beds": 60, "beds_per_10000": 1.5}
    )

    assert signal["signal_type"] == "balanced"
    assert signal["severity"] == "low"
    assert signal["mismatch_state"] == "balanced"


def test_gap_signal_insufficient_data():
    """Insufficient data when percentiles or core metrics are missing."""
    detector = GapSignalDetector()
    signal = detector.evaluate_sector_gap_signal(
        sector="healthcare",
        demand_percentile=None,
        infrastructure_percentile=None,
        demand_metrics={},
        infrastructure_metrics={}
    )

    assert signal["signal_type"] == "insufficient_data"
    assert signal["severity"] == "none"
    assert signal["mismatch_state"] == "insufficient_data"


# =============================================================================
# 7. Data Provenance Verification
# =============================================================================

def test_data_provenance_structure():
    """Verify that assembled intelligence records contain complete data provenance."""
    assembler = DistrictIntelligenceAssembler()
    record = assembler.assemble_sector_intelligence(
        district_id=str(uuid4()),
        district_name="Test District",
        state="Tamil Nadu",
        sector="healthcare",
        demographics={"population": 500000, "source": "Census 2011"},
        facilities=[{"capacity_value": {"facility_type": "Hospital", "beds": 50}}],
        indicators=[{"indicator_name": "NFHS5_INST_BIRTHS", "indicator_value": 92.0}],
        investments=[{"category": "healthcare", "amount": 50000000.0, "is_synthetic": True}],
        requests=[{"category": "healthcare", "created_at": datetime.now(timezone.utc).isoformat()}],
        clusters=None,
        demand_percentile=75.0,
        infrastructure_percentile=25.0
    )

    assert "data_sources" in record
    sources = {s["metric"]: s for s in record["data_sources"]}
    assert "Demographics & Population" in sources
    assert sources["Demographics & Population"]["is_synthetic"] is False
    assert "Healthcare Infrastructure" in sources
    assert sources["Healthcare Infrastructure"]["is_synthetic"] is False
    assert "Public Capital Investments" in sources
    assert sources["Public Capital Investments"]["is_synthetic"] is True
    assert "Citizen Grievances & Demand" in sources
    assert sources["Citizen Grievances & Demand"]["is_synthetic"] is True


# =============================================================================
# 8. Service End-to-End Refresh & In-Memory Store
# =============================================================================

def test_infrastructure_service_refresh_and_query():
    """Test full refresh and querying via InfrastructureIntelligenceService."""
    service = InfrastructureIntelligenceService()
    summary = service.refresh_all_intelligence()

    assert summary["success"] is True
    assert summary["total_records_generated"] > 0
    assert summary["districts_processed"] > 0

    # Retrieve all records
    records = service.list_district_intelligence()
    assert len(records) > 0

    # Retrieve gap signals
    gap_signals = service.get_gap_signals()
    assert isinstance(gap_signals, list)


# =============================================================================
# 9. FastAPI Infrastructure Intelligence Endpoints
# =============================================================================

def test_api_list_district_intelligence():
    """GET /api/infrastructure/districts returns list of district records with relative benchmarks."""
    response = client.get("/api/infrastructure/districts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "district_id" in item
        assert "sector" in item
        assert "demand_percentile" in item
        assert "infrastructure_percentile" in item
        assert "mismatch_signal" in item
        assert "data_sources" in item


def test_api_filter_by_sector():
    """GET /api/infrastructure/districts?sector=healthcare filters correctly."""
    response = client.get("/api/infrastructure/districts?sector=Healthcare")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert item["sector"].lower() == "healthcare"


def test_api_get_district_by_id():
    """GET /api/infrastructure/districts/{district_id} returns district details and sectors."""
    list_res = client.get("/api/infrastructure/districts")
    assert list_res.status_code == 200
    items = list_res.json()
    if len(items) > 0:
        target_id = items[0]["district_id"]
        res = client.get(f"/api/infrastructure/districts/{target_id}")
        assert res.status_code == 200
        detail = res.json()
        assert isinstance(detail, list)
        assert len(detail) > 0
        assert detail[0]["district_id"] == target_id

        # Test sectors endpoint
        sec_res = client.get(f"/api/infrastructure/districts/{target_id}/sectors")
        assert sec_res.status_code == 200
        sectors_data = sec_res.json()
        assert isinstance(sectors_data, dict)
        assert "sectors" in sectors_data
        assert isinstance(sectors_data["sectors"], list)
        assert any("sector" in s for s in sectors_data["sectors"])


def test_api_get_gap_signals():
    """GET /api/infrastructure/gap-signals returns explainable gap signals."""
    response = client.get("/api/infrastructure/gap-signals")
    assert response.status_code == 200
    signals = response.json()
    assert isinstance(signals, list)
    for sig in signals:
        assert "signal_type" in sig
        assert "severity" in sig
        assert "summary" in sig
        assert "evidence" in sig


def test_api_refresh_endpoint():
    """POST /api/infrastructure/refresh triggers re-calculation."""
    response = client.post("/api/infrastructure/refresh")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "total_records_generated" in res_data


# =============================================================================
# 10. Privacy & PII Protection Guarantees
# =============================================================================

def test_infrastructure_api_pii_isolation():
    """Verify that aggregate infrastructure endpoints never expose citizen personal info or raw requests."""
    response = client.get("/api/infrastructure/districts")
    assert response.status_code == 200
    raw_text = response.text

    # Verify no PII fields appear in response payload
    forbidden_keys = ["citizen_name", "phone_number", "email", "full_name", "phone", "aadhar", "voter_id"]
    for key in forbidden_keys:
        assert f'"{key}"' not in raw_text, f"Potential PII field '{key}' leaked in infrastructure endpoint"
