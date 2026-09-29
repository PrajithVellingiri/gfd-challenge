import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
from shapely.geometry import shape, Point

from app.config import settings
from app.db import get_db_connection

logger = logging.getLogger(__name__)

# Path to normalized districts dataset fallback
DISTRICTS_JSON_PATH = Path(__file__).parent.parent.parent.parent / "data" / "processed" / "districts_normalized.json"


class DistrictResolver:
    """
    Resolves geographic coordinates (lat, lon) to canonical district polygons.
    Uses PostGIS ST_Contains query when DB is reachable, with cached Shapely geometry fallback.
    """

    def __init__(self):
        self._cached_polygons = None

    def _load_cached_polygons(self):
        if self._cached_polygons is not None:
            return self._cached_polygons

        polygons = []
        if DISTRICTS_JSON_PATH.exists():
            try:
                data = json.loads(DISTRICTS_JSON_PATH.read_text(encoding="utf-8"))
                for d in data:
                    poly = shape(d["boundary"])
                    polygons.append({
                        "id": d["id"],
                        "name": d["name"],
                        "state": d["state"],
                        "country": d.get("country", "India"),
                        "geom": poly
                    })
            except Exception as e:
                logger.warning(f"Could not load local districts JSON for spatial fallback: {e}")

        self._cached_polygons = polygons
        return self._cached_polygons

    def resolve_district_by_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Performs spatial containment check for given lat/lon.
        Returns dict with district_id, district_name, state, resolved boolean.
        """
        # 1. Try PostGIS query via direct DB connection
        if settings.DATABASE_URL:
            conn = None
            try:
                conn = get_db_connection()
                if conn:
                    with conn.cursor() as cur:
                        # PostGIS ST_Contains takes (geometry, geometry)
                        cur.execute("""
                            SELECT id, name, state, country
                            FROM public.districts
                            WHERE boundary IS NOT NULL 
                              AND ST_Contains(boundary, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                            LIMIT 1;
                        """, (longitude, latitude))
                        row = cur.fetchone()
                        if row:
                            return {
                                "district_id": str(row["id"]),
                                "district_name": row["name"],
                                "state": row["state"],
                                "country": row.get("country", "India"),
                                "resolved": True,
                                "method": "postgis"
                            }
            except Exception as e:
                logger.debug(f"PostGIS district query fallback triggered: {e}")
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

        # 2. Shapely spatial fallback using normalized district polygons
        polygons = self._load_cached_polygons()
        pt = Point(longitude, latitude)
        for item in polygons:
            if item["geom"].contains(pt):
                return {
                    "district_id": item["id"],
                    "district_name": item["name"],
                    "state": item["state"],
                    "country": item["country"],
                    "resolved": True,
                    "method": "shapely_geojson"
                }

        # Point not within any known district boundary
        return {
            "district_id": None,
            "district_name": None,
            "state": None,
            "country": None,
            "resolved": False,
            "method": "none"
        }


district_resolver = DistrictResolver()
