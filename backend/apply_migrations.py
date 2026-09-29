#!/usr/bin/env python3
"""
GFD Challenge - Database Migration Runner
Applies SQL migrations sequentially to the target PostgreSQL / Supabase database.
"""
import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

MIGRATION_FILES = [
    "001_initial_schema.sql",
    "002_storage_setup.sql",
    "003_rls_policies.sql",
    "004_health_indicators.sql",
    "005_ai_analyses_enhancements.sql",
    "006_request_intelligence.sql",
]


def run_migrations(database_url: str = None) -> bool:
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable is not set.", file=sys.stderr)
        print("Please configure DATABASE_URL in your .env file or environment.", file=sys.stderr)
        return False

    print(f"[*] Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}", file=sys.stderr)
        return False

    # Create schema_migrations tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public._schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        );
    """)

    # Fetch applied migrations
    cursor.execute("SELECT version FROM public._schema_migrations;")
    applied_versions = {row[0] for row in cursor.fetchall()}

    success = True
    for filename in MIGRATION_FILES:
        filepath = MIGRATIONS_DIR / filename
        if not filepath.exists():
            print(f"[ERROR] Migration file not found: {filepath}", file=sys.stderr)
            success = False
            break

        if filename in applied_versions:
            print(f"[-] Migration already applied: {filename}")
            continue

        print(f"[+] Applying migration: {filename}...")
        try:
            sql_content = filepath.read_text(encoding="utf-8")
            cursor.execute(sql_content)
            cursor.execute(
                "INSERT INTO public._schema_migrations (version) VALUES (%s);",
                (filename,)
            )
            print(f"[OK] Successfully applied: {filename}")
        except Exception as e:
            print(f"[ERROR] Error applying migration {filename}: {e}", file=sys.stderr)
            success = False
            break

    cursor.close()
    conn.close()
    return success


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ok = run_migrations(url_arg)
    sys.exit(0 if ok else 1)
