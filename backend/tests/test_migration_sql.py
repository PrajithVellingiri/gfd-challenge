from pathlib import Path
import re
import pytest

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def read_migration(filename: str) -> str:
    path = MIGRATIONS_DIR / filename
    assert path.exists(), f"Migration file {filename} not found at {path}"
    return path.read_text(encoding="utf-8")


def test_migrations_exist():
    """
    Verifies that all three core migration files exist.
    """
    files = ["001_initial_schema.sql", "002_storage_setup.sql", "003_rls_policies.sql"]
    for f in files:
        assert (MIGRATIONS_DIR / f).exists(), f"Missing migration file {f}"


def test_001_initial_schema_contents():
    """
    Verifies PostGIS, core tables, geometry columns, spatial indexes, and triggers in 001_initial_schema.sql.
    """
    sql = read_migration("001_initial_schema.sql").lower()

    # 1. PostGIS extension
    assert 'create extension if not exists "postgis"' in sql or "create extension if not exists postgis" in sql

    # 2. Required tables
    required_tables = [
        "public.users",
        "public.districts",
        "public.citizen_requests",
        "public.infrastructure",
        "public.demographics",
        "public.investments",
        "public.ai_analyses"
    ]
    for table in required_tables:
        assert f"create table if not exists {table}" in sql, f"Missing table definition: {table}"

    # 3. PostGIS geometry and geography columns
    assert "geography(point, 4326)" in sql
    assert "geometry(multipolygon, 4326)" in sql
    assert "geometry(point, 4326)" in sql

    # 4. Spatial GIST indexes
    assert "idx_citizen_requests_location" in sql
    assert "using gist (location)" in sql
    assert "idx_infrastructure_location" in sql
    assert "idx_districts_boundary" in sql
    assert "using gist (boundary)" in sql
    assert "idx_districts_centroid" in sql
    assert "using gist (centroid)" in sql

    # 5. Coordinate sync trigger
    assert "sync_citizen_request_location" in sql
    assert "sync_infrastructure_location" in sql

    # 6. Future-proofing AI columns in citizen_requests
    assert "extracted_intent" in sql
    assert "ai_category" in sql
    assert "ai_confidence" in sql
    assert "extracted_entities" in sql
    assert "ai_analysis" in sql
    assert "cluster_id" in sql

    # 7. Multi-country support
    assert "country" in sql


def test_002_storage_setup_contents():
    """
    Verifies storage buckets (citizen-images, citizen-audio), private visibility, and storage RLS.
    """
    sql = read_migration("002_storage_setup.sql").lower()

    # Buckets
    assert "'citizen-images'" in sql
    assert "'citizen-audio'" in sql
    # Private buckets
    assert "false" in sql  # public = false

    # Storage RLS policies
    assert "storage.objects" in sql
    assert "storage.foldername(name)" in sql
    assert "auth.uid()::text" in sql
    assert "citizens can upload own files" in sql
    assert "citizens can view own files" in sql
    assert "staff can view all citizen files" in sql


def test_003_rls_policies_contents():
    """
    Verifies Row Level Security enablement and policies on all tables.
    """
    sql = read_migration("003_rls_policies.sql").lower()

    # RLS enablement
    tables = [
        "public.users",
        "public.citizen_requests",
        "public.districts",
        "public.infrastructure",
        "public.demographics",
        "public.investments",
        "public.ai_analyses"
    ]
    for table in tables:
        assert f"alter table {table} enable row level security;" in sql, f"RLS not enabled on {table}"

    # Helper function & Auth Hook
    assert "get_current_user_role" in sql
    assert "handle_new_user" in sql
    assert "on_auth_user_created" in sql

    # Citizen isolation policies
    assert "citizens can create their own requests" in sql
    assert "citizens can view their own requests" in sql
    assert "policymaker" in sql
    assert "admin" in sql
