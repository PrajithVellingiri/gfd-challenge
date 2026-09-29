#!/usr/bin/env python3
"""
Master Database Ingestion Script
Batch-loads all normalized Phase 2 datasets into Supabase PostgreSQL / PostGIS.
Uses psycopg2 batch execution for high-throughput insertion.
Supports idempotent upserts and dry-run mode.
"""
import os
import sys
import json
import psycopg2
from psycopg2.extras import execute_values, Json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DIR = Path(__file__).parent.parent / "processed"


def get_db_connection(database_url: str = None):
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        return None
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}", file=sys.stderr)
        return None


def load_json(filename: str):
    path = PROCESSED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Processed file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_districts(conn):
    districts = load_json("districts_normalized.json")
    print(f"[*] Ingesting {len(districts)} districts...")
    query = """
        INSERT INTO public.districts (id, name, state, country, population_ref, boundary, centroid)
        VALUES %s
        ON CONFLICT (name, state, country) DO UPDATE SET
            population_ref = EXCLUDED.population_ref,
            boundary = EXCLUDED.boundary,
            centroid = EXCLUDED.centroid;
    """
    records = []
    for d in districts:
        geom_json = json.dumps(d["boundary"])
        centroid_wkt = f"POINT({d['centroid']['longitude']} {d['centroid']['latitude']})"
        records.append((
            d["id"],
            d["name"],
            d["state"],
            d["country"],
            d["population_ref"],
            geom_json,
            centroid_wkt
        ))

    # Use template with PostGIS geometry construction
    template = "(%s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), ST_SetSRID(ST_GeomFromText(%s), 4326))"
    with conn.cursor() as cur:
        execute_values(cur, query, records, template=template)
    conn.commit()
    print(f"[OK] Ingested {len(districts)} districts.")


def load_demographics(conn):
    demographics = load_json("demographics_normalized.json")
    print(f"[*] Ingesting {len(demographics)} demographics records...")
    query = """
        INSERT INTO public.demographics (district_id, population, rural_population, urban_population, demographic_indicators, year, source, data_type)
        VALUES %s
        ON CONFLICT (district_id, year) DO UPDATE SET
            population = EXCLUDED.population,
            rural_population = EXCLUDED.rural_population,
            urban_population = EXCLUDED.urban_population,
            demographic_indicators = EXCLUDED.demographic_indicators,
            data_type = EXCLUDED.data_type;
    """
    records = [
        (
            d["district_id"],
            d["population"],
            d["rural_population"],
            d["urban_population"],
            Json(d["demographic_indicators"]),
            d["year"],
            d["source"],
            d.get("data_type", "official")
        )
        for d in demographics
    ]
    with conn.cursor() as cur:
        execute_values(cur, query, records)
    conn.commit()
    print(f"[OK] Ingested {len(demographics)} demographics records.")


def load_infrastructure(conn):
    infra = load_json("infrastructure_normalized.json")
    print(f"[*] Ingesting {len(infra)} infrastructure facilities...")
    query = """
        INSERT INTO public.infrastructure (district_id, category, name, latitude, longitude, capacity_value, source, source_reference, data_type)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    records = [
        (
            i["district_id"],
            i["category"],
            i["name"],
            i.get("latitude"),
            i.get("longitude"),
            Json(i.get("capacity_value", {})),
            i.get("source"),
            i.get("source_reference"),
            i.get("data_type", "official")
        )
        for i in infra
    ]
    with conn.cursor() as cur:
        execute_values(cur, query, records)
    conn.commit()
    print(f"[OK] Ingested {len(infra)} infrastructure facilities.")


def load_health_indicators(conn):
    health_ind = load_json("health_indicators_normalized.json")
    print(f"[*] Ingesting {len(health_ind)} health indicators...")
    query = """
        INSERT INTO public.health_indicators (district_id, indicator_name, indicator_value, unit, year, source, source_reference, metadata)
        VALUES %s
        ON CONFLICT (district_id, indicator_name, year) DO UPDATE SET
            indicator_value = EXCLUDED.indicator_value,
            metadata = EXCLUDED.metadata;
    """
    records = [
        (
            h["district_id"],
            h["indicator_name"],
            h["indicator_value"],
            h["unit"],
            h["year"],
            h["source"],
            h["source_reference"],
            Json(h.get("metadata", {}))
        )
        for h in health_ind
    ]
    with conn.cursor() as cur:
        execute_values(cur, query, records)
    conn.commit()
    print(f"[OK] Ingested {len(health_ind)} health indicators.")


def load_investments(conn):
    investments = load_json("investments_normalized.json")
    print(f"[*] Ingesting {len(investments)} investment records...")
    query = """
        INSERT INTO public.investments (district_id, category, amount, currency, financial_year, source, source_reference, data_type)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    records = [
        (
            inv["district_id"],
            inv["category"],
            inv["amount"],
            inv["currency"],
            inv["financial_year"],
            inv["source"],
            inv.get("source_reference"),
            inv.get("data_type", "synthetic")
        )
        for inv in investments
    ]
    with conn.cursor() as cur:
        execute_values(cur, query, records)
    conn.commit()
    print(f"[OK] Ingested {len(investments)} investment records.")


def load_citizen_requests(conn, chunk_size=1000):
    requests = load_json("citizen_requests_normalized.json")
    total = len(requests)
    print(f"[*] Ingesting {total} citizen demand requests in batches of {chunk_size}...")

    query = """
        INSERT INTO public.citizen_requests (
            id, district_id, category, description, language, urgency, status,
            latitude, longitude, location_name, source_type, is_synthetic, data_type,
            created_at, updated_at
        ) VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """

    with conn.cursor() as cur:
        for i in range(0, total, chunk_size):
            chunk = requests[i:i + chunk_size]
            records = [
                (
                    r["id"],
                    r["district_id"],
                    r["category"],
                    r["description"],
                    r["language"],
                    r["urgency"],
                    r["status"],
                    r["latitude"],
                    r["longitude"],
                    r["location_name"],
                    r.get("source_type", "web"),
                    r.get("is_synthetic", True),
                    r.get("data_type", "synthetic"),
                    r["created_at"],
                    r["updated_at"]
                )
                for r in chunk
            ]
            execute_values(cur, query, records)
            print(f"    Batch {i // chunk_size + 1}: Ingested {len(records)} requests ({min(i + chunk_size, total)}/{total})")
    conn.commit()
    print(f"[OK] Ingested all {total} citizen requests.")


def load_all(database_url: str = None, dry_run: bool = False):
    if dry_run:
        print("[*] Running in DRY-RUN mode. Validating files without database connection...")
        for fn in ["districts_normalized.json", "demographics_normalized.json", "infrastructure_normalized.json", "health_indicators_normalized.json", "investments_normalized.json", "citizen_requests_normalized.json"]:
            data = load_json(fn)
            print(f"    [OK] File validated: {fn} ({len(data)} records)")
        print("[OK] Dry-run validation passed.")
        return True

    conn = get_db_connection(database_url)
    if not conn:
        print("[WARN] DATABASE_URL not set or unreachable. Skipping live database insertion.")
        print("To load into database, provide DATABASE_URL in .env and rerun this script.")
        return False

    try:
        load_districts(conn)
        load_demographics(conn)
        load_infrastructure(conn)
        load_health_indicators(conn)
        load_investments(conn)
        load_citizen_requests(conn)
        print("[OK] All Phase 2 datasets successfully loaded into database.")
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    url_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("postgresql://") or arg.startswith("postgres://"):
            url_arg = arg
    load_all(url_arg, dry_run=is_dry)
