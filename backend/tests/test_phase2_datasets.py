import json
from pathlib import Path
import pytest
from shapely.geometry import shape

from data.scripts.district_normalizer import district_normalizer
from data.schemas.dataset_schemas import (
    DistrictModel,
    DemographicsModel,
    InfrastructureModel,
    HealthIndicatorModel,
    InvestmentModel,
    CitizenDemandModel
)

REPO_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
RAW_DIR = REPO_ROOT / "data" / "raw"
DATA_DIR = REPO_ROOT / "data"


def load_processed_json(filename: str):
    path = PROCESSED_DIR / filename
    assert path.exists(), f"Processed dataset {path} does not exist."
    return json.loads(path.read_text(encoding="utf-8"))


def test_dataset_files_and_registry_exist():
    """
    Verifies that all required raw and processed files and documentation exist.
    """
    assert (DATA_DIR / "DATA_SOURCES.md").exists(), "Missing DATA_SOURCES.md"
    assert (DATA_DIR / "README.md").exists(), "Missing data/README.md"

    expected_processed = [
        "districts_normalized.json",
        "demographics_normalized.json",
        "infrastructure_normalized.json",
        "health_indicators_normalized.json",
        "investments_normalized.json",
        "citizen_requests_normalized.json"
    ]
    for fn in expected_processed:
        assert (PROCESSED_DIR / fn).exists(), f"Missing processed file: {fn}"


def test_district_normalizer_aliases_and_determinism():
    """
    Verifies that the normalizer accurately maps aliases, historical names, and generates deterministic UUIDs.
    """
    cases = [
        ("Bangalore", "Karnataka", "Bengaluru Urban"),
        ("bengaluru", "karnataka", "Bengaluru Urban"),
        ("Madras", "Tamil Nadu", "Chennai"),
        ("Poona", "Maharashtra", "Pune"),
        ("Baroda", "Gujarat", "Vadodara"),
        ("Gulbarga", "Karnataka", "Kalaburagi"),
        ("Benares", "Uttar Pradesh", "Varanasi"),
        ("Kovai", "Tamil Nadu", "Coimbatore"),
        ("Cochin", "Kerala", "Ernakulam"),
    ]
    for raw_dist, raw_st, expected_dist in cases:
        norm = district_normalizer.normalize(raw_dist, raw_st)
        assert norm["district_name"] == expected_dist
        assert norm["matched"] is True

    # Test deterministic UUID generation
    id1 = district_normalizer.normalize("Bangalore", "Karnataka")["district_id"]
    id2 = district_normalizer.normalize("Bengaluru Urban", "Karnataka")["district_id"]
    assert id1 == id2, "Canonical UUID must be identical for alias variations."


def test_geographic_gis_polygons_valid():
    """
    Verifies district geometries are valid EPSG:4326 polygons with valid centroids.
    """
    districts = load_processed_json("districts_normalized.json")
    assert len(districts) >= 30, f"Expected at least 30 representative districts, found {len(districts)}"

    for d in districts:
        model = DistrictModel(**d)
        geom = shape(model.boundary)
        assert geom.is_valid, f"Invalid geometry polygon in district {model.name}"
        assert not geom.is_empty
        # Verify coordinates fall within India bounds
        min_lon, min_lat, max_lon, max_lat = model.bbox
        assert 68.0 <= min_lon <= 98.0
        assert 6.0 <= min_lat <= 38.0
        assert 68.0 <= model.centroid["longitude"] <= 98.0
        assert 6.0 <= model.centroid["latitude"] <= 38.0


def test_demographics_quality_and_schema():
    """
    Verifies demographics conform to schema, official classification, and math sanity.
    """
    records = load_processed_json("demographics_normalized.json")
    for r in records:
        model = DemographicsModel(**r)
        assert model.population > 0
        assert model.rural_population + model.urban_population == model.population
        assert model.data_type == "official"
        assert model.year == 2011
        assert "Census of India" in model.source


def test_healthcare_infrastructure_quality():
    """
    Verifies healthcare facilities have valid categories, non-negative capacity, and coordinates.
    """
    infra = load_processed_json("infrastructure_normalized.json")
    assert len(infra) >= 40
    for item in infra:
        model = InfrastructureModel(**item)
        assert model.category == "healthcare"
        assert model.data_type == "official"
        assert model.capacity_value.get("bed_count", 0) >= 0
        if model.latitude and model.longitude:
            assert 6.0 <= model.latitude <= 38.0
            assert 68.0 <= model.longitude <= 98.0


def test_health_indicators_quality():
    """
    Verifies NFHS-5 health indicators are within [0, 100]%, have official provenance.
    """
    indicators = load_processed_json("health_indicators_normalized.json")
    assert len(indicators) >= 200
    for ind in indicators:
        model = HealthIndicatorModel(**ind)
        assert 0.0 <= model.indicator_value <= 100.0
        assert model.unit == "%"
        assert model.data_type == "official"
        assert model.year == 2020


def test_investments_synthetic_transparency():
    """
    Ensures investment dataset is explicitly marked synthetic and cannot be mistaken for official data.
    """
    investments = load_processed_json("investments_normalized.json")
    for inv in investments:
        model = InvestmentModel(**inv)
        assert model.data_type == "synthetic"
        assert model.source == "demo-generated"
        assert model.amount >= 0
        assert model.currency == "INR"


def test_citizen_requests_hotspots_and_provenance():
    """
    Verifies citizen requests meet size (5k-20k), category, coordinate, and hotspot requirements.
    """
    requests = load_processed_json("citizen_requests_normalized.json")
    assert 5000 <= len(requests) <= 20000, f"Citizen requests count {len(requests)} outside target [5000, 20000]"

    categories_count = {}
    bahraich_categories = {}

    for req in requests:
        model = CitizenDemandModel(**req)
        assert model.is_synthetic is True
        assert model.data_type == "synthetic"
        assert 6.0 <= model.latitude <= 38.0
        assert 68.0 <= model.longitude <= 98.0
        categories_count[model.category] = categories_count.get(model.category, 0) + 1

        if model.district_name == "Bahraich":
            bahraich_categories[model.category] = bahraich_categories.get(model.category, 0) + 1

    # Verify all 7 required sectors are present
    required_cats = {
        "healthcare", "education", "roads", "water",
        "transportation", "electricity", "digital infrastructure"
    }
    assert set(categories_count.keys()) == required_cats

    # Verify intentional hotspot in Bahraich (healthcare demand is dominant)
    assert bahraich_categories.get("healthcare", 0) > bahraich_categories.get("electricity", 0)


def test_foreign_key_referential_integrity():
    """
    Verifies that every record across Demographics, Infrastructure, Health Indicators,
    Investments, and Citizen Requests references a valid canonical district ID.
    """
    districts = load_processed_json("districts_normalized.json")
    valid_district_ids = {d["id"] for d in districts}

    demographics = load_processed_json("demographics_normalized.json")
    for d in demographics:
        assert d["district_id"] in valid_district_ids

    infra = load_processed_json("infrastructure_normalized.json")
    for i in infra:
        assert i["district_id"] in valid_district_ids

    health_ind = load_processed_json("health_indicators_normalized.json")
    for h in health_ind:
        assert h["district_id"] in valid_district_ids

    investments = load_processed_json("investments_normalized.json")
    for inv in investments:
        assert inv["district_id"] in valid_district_ids

    citizen_reqs = load_processed_json("citizen_requests_normalized.json")
    for cr in citizen_reqs:
        assert cr["district_id"] in valid_district_ids


def test_migration_004_sql_content():
    """
    Verifies 004_health_indicators.sql contains table, columns, indexes, and RLS.
    """
    migration_path = REPO_ROOT / "backend" / "migrations" / "004_health_indicators.sql"
    assert migration_path.exists(), "Missing 004_health_indicators.sql migration"
    sql = migration_path.read_text(encoding="utf-8").lower()

    assert "create table if not exists public.health_indicators" in sql
    assert "enable row level security" in sql
    assert "add column if not exists district_id" in sql
    assert "add column if not exists is_synthetic" in sql
    assert "add column if not exists data_type" in sql
