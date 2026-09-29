import json
import logging
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings

logger = logging.getLogger(__name__)

# Cached Supabase client
_supabase_client = None


def get_supabase_client():
    """
    Returns an initialized Supabase Client if credentials are provided.
    Lazy-loads the client to avoid crash if env vars are unset during development/testing.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY):
        try:
            from supabase import create_client, Client
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
            _supabase_client = create_client(settings.SUPABASE_URL, key)
            return _supabase_client
        except Exception as e:
            logger.warning(f"Could not initialize Supabase client: {e}")
            return None
    return None


def get_db_connection():
    """
    Returns a psycopg2 database connection using DATABASE_URL if configured.
    """
    if not settings.DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error("Database connection failure")
        return None


def check_db_health() -> Dict[str, Any]:
    """
    Verifies database connectivity without leaking credentials.
    Returns status dict with 'connected' boolean and message.
    """
    # Try direct Postgres connection first if DATABASE_URL is set
    if settings.DATABASE_URL:
        conn = None
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS alive;")
                    res = cur.fetchone()
                    if res and res.get("alive") == 1:
                        return {"connected": True, "provider": "postgresql", "message": "PostgreSQL reachable"}
        except Exception as e:
            logger.warning(f"PostgreSQL direct check failed: {type(e).__name__}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # Fall back to Supabase client ping
    client = get_supabase_client()
    if client:
        try:
            # Query a basic table to confirm reachability
            res = client.table("districts").select("id").limit(1).execute()
            return {"connected": True, "provider": "supabase", "message": "Supabase reachable"}
        except Exception as e:
            logger.warning(f"Supabase client check failed: {type(e).__name__}")
            # If table not yet created or connection error, check if client was built
            return {"connected": False, "provider": "supabase", "message": "Supabase client configured but query failed"}

    if not settings.DATABASE_URL and not settings.SUPABASE_URL:
        return {"connected": False, "provider": "unconfigured", "message": "No database credentials configured"}

    return {"connected": False, "provider": "unknown", "message": "Database unreachable"}


def insert_citizen_request(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Inserts a citizen request into the database via direct connection or Supabase client.
    """
    # 1. Try Supabase client if available
    client = get_supabase_client()
    if client:
        try:
            res = client.table("citizen_requests").insert(request_data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error inserting request via Supabase: {type(e).__name__}")

    # 2. Try direct PostgreSQL
    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    columns = list(request_data.keys())
                    values = [request_data[c] for c in columns]
                    col_names = ", ".join(f'"{c}"' for c in columns)
                    placeholders = ", ".join(["%s"] * len(values))
                    query = f"INSERT INTO public.citizen_requests ({col_names}) VALUES ({placeholders}) RETURNING *;"
                    cur.execute(query, values)
                    row = cur.fetchone()
                    conn.commit()
                    return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error inserting request via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return None


def fetch_citizen_request(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single citizen request by ID.
    """
    # 1. Try Supabase
    client = get_supabase_client()
    if client:
        try:
            res = client.table("citizen_requests").select("*").eq("id", request_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching request via Supabase: {type(e).__name__}")

    # 2. Try direct PostgreSQL
    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM public.citizen_requests WHERE id = %s;", (request_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error fetching request via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return None


def list_citizen_requests(user_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lists citizen requests with optional user_id filter and pagination.
    """
    client = get_supabase_client()
    if client:
        try:
            query = client.table("citizen_requests").select("*").range(offset, offset + limit - 1)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error listing requests via Supabase: {type(e).__name__}")

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute(
                            "SELECT * FROM public.citizen_requests WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s;",
                            (user_id, limit, offset)
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM public.citizen_requests ORDER BY created_at DESC LIMIT %s OFFSET %s;",
                            (limit, offset)
                        )
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
            except Exception as e:
                logger.error(f"Error listing requests via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return []


def upsert_ai_analysis(analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Inserts or updates an AI analysis record for a given request_id.
    """
    req_id = analysis_data.get("request_id")
    if not req_id:
        return None

    # 1. Try Supabase Client
    client = get_supabase_client()
    if client:
        try:
            # Check if record already exists
            existing = client.table("ai_analyses").select("id").eq("request_id", str(req_id)).limit(1).execute()
            if existing.data and len(existing.data) > 0:
                row_id = existing.data[0]["id"]
                res = client.table("ai_analyses").update(analysis_data).eq("id", row_id).execute()
                if res.data:
                    return res.data[0]
            else:
                res = client.table("ai_analyses").insert(analysis_data).execute()
                if res.data:
                    return res.data[0]
        except Exception as e:
            logger.error(f"Error upserting AI analysis via Supabase: {type(e).__name__}")

    # 2. Try direct PostgreSQL
    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if exists
                    cur.execute("SELECT id FROM public.ai_analyses WHERE request_id = %s LIMIT 1;", (str(req_id),))
                    row = cur.fetchone()

                    # Prepare columns and values
                    cols = list(analysis_data.keys())
                    vals = []
                    for c in cols:
                        v = analysis_data[c]
                        if isinstance(v, (dict, list)):
                            vals.append(json.dumps(v))
                        else:
                            vals.append(v)

                    if row:
                        # UPDATE
                        set_clause = ", ".join(f'"{c}" = %s' for c in cols)
                        vals.append(row["id"])
                        query = f"UPDATE public.ai_analyses SET {set_clause}, updated_at = now() WHERE id = %s RETURNING *;"
                        cur.execute(query, vals)
                    else:
                        # INSERT
                        col_names = ", ".join(f'"{c}"' for c in cols)
                        placeholders = ", ".join(["%s"] * len(vals))
                        query = f"INSERT INTO public.ai_analyses ({col_names}) VALUES ({placeholders}) RETURNING *;"
                        cur.execute(query, vals)

                    updated = cur.fetchone()
                    conn.commit()
                    return dict(updated) if updated else None
            except Exception as e:
                logger.error(f"Error upserting AI analysis via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    # Fallback in-memory return for testing without db
    return analysis_data


def fetch_ai_analysis(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the AI analysis record for a given request_id.
    """
    client = get_supabase_client()
    if client:
        try:
            res = client.table("ai_analyses").select("*").eq("request_id", str(request_id)).order("created_at", desc=True).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching AI analysis via Supabase: {type(e).__name__}")

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM public.ai_analyses WHERE request_id = %s ORDER BY created_at DESC LIMIT 1;",
                        (str(request_id),)
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error fetching AI analysis via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return None

