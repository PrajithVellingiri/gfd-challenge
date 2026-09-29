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


# =============================================================================
# Phase 5: Request Intelligence Database Operations
# =============================================================================

# In-memory stores for testing / offline mode
_memory_embeddings = {}
_memory_similarities = []
_memory_clusters = []
_memory_emerging_issues = []


def save_request_embedding(
    request_id: str,
    embedding: List[float],
    model_name: str = "models/text-embedding-004",
    version: str = "v1.0"
) -> bool:
    """Saves or updates 768-dim semantic embedding for a request."""
    req_id = str(request_id)
    _memory_embeddings[req_id] = {
        "request_id": req_id,
        "embedding": embedding,
        "embedding_model": model_name,
        "embedding_version": version
    }

    client = get_supabase_client()
    if client:
        try:
            client.table("request_embeddings").upsert({
                "request_id": req_id,
                "embedding": embedding,
                "embedding_model": model_name,
                "embedding_version": version
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving embedding via Supabase: {type(e).__name__}")

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    vec_str = "[" + ",".join(str(f) for f in embedding) + "]"
                    cur.execute("""
                        INSERT INTO public.request_embeddings (request_id, embedding, embedding_model, embedding_version)
                        VALUES (%s, %s::vector, %s, %s)
                        ON CONFLICT (request_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            embedding_model = EXCLUDED.embedding_model,
                            embedding_version = EXCLUDED.embedding_version;
                    """, (req_id, vec_str, model_name, version))
                    conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error saving embedding via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return True


def fetch_request_embedding(request_id: str) -> Optional[List[float]]:
    """Retrieves embedding vector for a request."""
    req_id = str(request_id)
    if req_id in _memory_embeddings:
        return _memory_embeddings[req_id]["embedding"]

    client = get_supabase_client()
    if client:
        try:
            res = client.table("request_embeddings").select("embedding").eq("request_id", req_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                raw = res.data[0]["embedding"]
                if isinstance(raw, list):
                    return raw
                elif isinstance(raw, str):
                    return [float(x.strip()) for x in raw.strip("[]").split(",") if x.strip()]
        except Exception as e:
            logger.error(f"Error fetching embedding via Supabase: {type(e).__name__}")

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT embedding FROM public.request_embeddings WHERE request_id = %s;", (req_id,))
                    row = cur.fetchone()
                    if row and row.get("embedding"):
                        raw = row["embedding"]
                        if isinstance(raw, list):
                            return raw
                        elif isinstance(raw, str):
                            return [float(x.strip()) for x in raw.strip("[]").split(",") if x.strip()]
            except Exception as e:
                logger.error(f"Error fetching embedding via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return None


def list_request_embeddings_with_meta(limit: int = 1000) -> List[Dict[str, Any]]:
    """Fetches candidate request embeddings with their category, sub-category, and district metadata."""
    results = []
    # Include memory embeddings
    for r_id, item in _memory_embeddings.items():
        req_rec = fetch_citizen_request(r_id) or {}
        ai_rec = fetch_ai_analysis(r_id) or {}
        results.append({
            "request_id": r_id,
            "embedding": item["embedding"],
            "category": ai_rec.get("category") or req_rec.get("category"),
            "sub_category": ai_rec.get("sub_category"),
            "district_id": req_rec.get("district_id"),
            "latitude": req_rec.get("latitude"),
            "longitude": req_rec.get("longitude"),
            "location_name": req_rec.get("location_name"),
            "created_at": req_rec.get("created_at")
        })

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            e.request_id,
                            e.embedding,
                            COALESCE(a.category, r.category) AS category,
                            a.sub_category,
                            r.district_id,
                            r.latitude,
                            r.longitude,
                            r.location_name,
                            r.created_at
                        FROM public.request_embeddings e
                        JOIN public.citizen_requests r ON e.request_id = r.id
                        LEFT JOIN public.ai_analyses a ON r.id = a.request_id
                        LIMIT %s;
                    """, (limit,))
                    rows = cur.fetchall()
                    for row in rows:
                        raw = row["embedding"]
                        vec = [float(x.strip()) for x in raw.strip("[]").split(",") if x.strip()] if isinstance(raw, str) else raw
                        # Avoid duplicates from in-memory
                        if not any(str(x["request_id"]) == str(row["request_id"]) for x in results):
                            results.append({
                                "request_id": str(row["request_id"]),
                                "embedding": vec,
                                "category": row["category"],
                                "sub_category": row["sub_category"],
                                "district_id": str(row["district_id"]) if row["district_id"] else None,
                                "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
                                "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
                                "location_name": row["location_name"],
                                "created_at": str(row["created_at"]) if row["created_at"] else None
                            })
            except Exception as e:
                logger.error(f"Error listing embeddings via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return results


def save_request_similarity(
    source_request_id: str,
    target_request_id: str,
    similarity_score: float,
    relationship_type: str
) -> bool:
    """Records similarity or duplicate edge between two requests."""
    src = str(source_request_id)
    tgt = str(target_request_id)
    if src == tgt:
        return False

    _memory_similarities.append({
        "source_request_id": src,
        "target_request_id": tgt,
        "similarity_score": round(similarity_score, 4),
        "relationship_type": relationship_type
    })

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO public.request_similarities 
                        (source_request_id, target_request_id, similarity_score, relationship_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source_request_id, target_request_id) DO UPDATE SET
                            similarity_score = EXCLUDED.similarity_score,
                            relationship_type = EXCLUDED.relationship_type;
                    """, (src, tgt, similarity_score, relationship_type))
                    conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error saving similarity via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return True


def fetch_request_similarities(
    request_id: str,
    relationship_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves similarity records for a request."""
    req_id = str(request_id)
    results = []

    for item in _memory_similarities:
        if (item["source_request_id"] == req_id or item["target_request_id"] == req_id):
            if not relationship_type or item["relationship_type"] == relationship_type:
                other_id = item["target_request_id"] if item["source_request_id"] == req_id else item["source_request_id"]
                results.append({
                    "request_id": other_id,
                    "similarity_score": item["similarity_score"],
                    "relationship_type": item["relationship_type"]
                })

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT 
                            CASE WHEN source_request_id = %s THEN target_request_id ELSE source_request_id END AS request_id,
                            similarity_score,
                            relationship_type,
                            created_at
                        FROM public.request_similarities
                        WHERE (source_request_id = %s OR target_request_id = %s)
                    """
                    params = [req_id, req_id, req_id]
                    if relationship_type:
                        query += " AND relationship_type = %s"
                        params.append(relationship_type)
                    query += " ORDER BY similarity_score DESC LIMIT 50;"
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    for r in rows:
                        rid = str(r["request_id"])
                        if not any(x["request_id"] == rid for x in results):
                            results.append({
                                "request_id": rid,
                                "similarity_score": float(r["similarity_score"]),
                                "relationship_type": r["relationship_type"],
                                "created_at": str(r["created_at"]) if r.get("created_at") else None
                            })
            except Exception as e:
                logger.error(f"Error fetching similarities via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return results


def save_clusters(clusters: List[Dict[str, Any]]) -> bool:
    """Saves clusters and their memberships to database."""
    global _memory_clusters
    _memory_clusters = clusters

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    for cl in clusters:
                        cl_id = cl["id"]
                        cur.execute("""
                            INSERT INTO public.request_clusters (id, cluster_label, category, district_id, request_count, summary)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                cluster_label = EXCLUDED.cluster_label,
                                category = EXCLUDED.category,
                                district_id = EXCLUDED.district_id,
                                request_count = EXCLUDED.request_count,
                                summary = EXCLUDED.summary,
                                updated_at = now();
                        """, (cl_id, cl["cluster_label"], cl["category"], cl["district_id"], cl["request_count"], cl["summary"]))

                        for mem in cl.get("member_requests", []):
                            cur.execute("""
                                INSERT INTO public.cluster_memberships (cluster_id, request_id, similarity_score)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (cluster_id, request_id) DO UPDATE SET
                                    similarity_score = EXCLUDED.similarity_score;
                            """, (cl_id, mem["request_id"], mem.get("similarity_score", 1.0)))

                    conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error saving clusters via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return True


def fetch_clusters(
    district_id: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves cluster list with optional filters."""
    matches = []
    for c in _memory_clusters:
        if district_id and str(c.get("district_id")) != str(district_id):
            continue
        if category and str(c.get("category", "")).lower() != category.lower():
            continue
        matches.append(c)

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    query = "SELECT * FROM public.request_clusters WHERE 1=1"
                    params = []
                    if district_id:
                        query += " AND district_id = %s"
                        params.append(district_id)
                    if category:
                        query += " AND LOWER(category) = LOWER(%s)"
                        params.append(category)
                    query += " ORDER BY request_count DESC LIMIT 100;"
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    for r in rows:
                        cid = str(r["id"])
                        if not any(x["id"] == cid for x in matches):
                            matches.append({
                                "id": cid,
                                "cluster_label": r["cluster_label"],
                                "category": r["category"],
                                "district_id": str(r["district_id"]) if r["district_id"] else None,
                                "request_count": r["request_count"],
                                "summary": r["summary"],
                                "created_at": str(r["created_at"]) if r.get("created_at") else None
                            })
            except Exception as e:
                logger.error(f"Error fetching clusters via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return matches


def save_emerging_issues(issues: List[Dict[str, Any]]) -> bool:
    """Saves detected emerging issues to database."""
    global _memory_emerging_issues
    _memory_emerging_issues = issues

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    for iss in issues:
                        cur.execute("""
                            INSERT INTO public.emerging_issues 
                            (id, title, description, category, district_id, current_count, previous_count, growth_percentage, indicator)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                title = EXCLUDED.title,
                                description = EXCLUDED.description,
                                current_count = EXCLUDED.current_count,
                                previous_count = EXCLUDED.previous_count,
                                growth_percentage = EXCLUDED.growth_percentage,
                                indicator = EXCLUDED.indicator,
                                updated_at = now();
                        """, (
                            iss["id"], iss["title"], iss.get("description"), iss["category"],
                            iss.get("district_id"), iss["current_count"], iss["previous_count"],
                            iss.get("growth_percentage"), iss["indicator"]
                        ))
                    conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error saving emerging issues via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return True


def fetch_emerging_issues(
    district_id: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves emerging issues with optional filters."""
    matches = []
    for iss in _memory_emerging_issues:
        if district_id and str(iss.get("district_id")) != str(district_id):
            continue
        if category and str(iss.get("category", "")).lower() != category.lower():
            continue
        matches.append(iss)

    if settings.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    query = "SELECT * FROM public.emerging_issues WHERE 1=1"
                    params = []
                    if district_id:
                        query += " AND district_id = %s"
                        params.append(district_id)
                    if category:
                        query += " AND LOWER(category) = LOWER(%s)"
                        params.append(category)
                    query += " ORDER BY current_count DESC LIMIT 100;"
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    for r in rows:
                        iid = str(r["id"])
                        if not any(x["id"] == iid for x in matches):
                            matches.append({
                                "id": iid,
                                "title": r["title"],
                                "description": r["description"],
                                "category": r["category"],
                                "district_id": str(r["district_id"]) if r["district_id"] else None,
                                "current_count": r["current_count"],
                                "previous_count": r["previous_count"],
                                "growth_percentage": float(r["growth_percentage"]) if r["growth_percentage"] is not None else None,
                                "indicator": r["indicator"],
                                "created_at": str(r["created_at"]) if r.get("created_at") else None,
                                "signal_type": "AI/data-derived signal (advisory governance triage)"
                            })
            except Exception as e:
                logger.error(f"Error fetching emerging issues via PostgreSQL: {type(e).__name__}")
            finally:
                conn.close()

    return matches


