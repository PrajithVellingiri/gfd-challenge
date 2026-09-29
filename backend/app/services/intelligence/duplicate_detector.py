"""
Duplicate Detection Service (Phase 5).
Distinguishes true duplicates/near-duplicates from geographically separate similar requests.
Enforces location awareness and transparent explainability.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
from app.config import settings

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates approximate great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def are_locations_coincident(
    req_a: Dict[str, Any],
    req_b: Dict[str, Any],
    max_distance_km: float = 15.0
) -> Tuple[bool, str]:
    """
    Evaluates whether two requests share the same geographic locality.
    Checks exact district match or GPS coordinate proximity (< max_distance_km).
    """
    dist_a = str(req_a.get("district_id") or "")
    dist_b = str(req_b.get("district_id") or "")

    lat_a = req_a.get("latitude")
    lon_a = req_a.get("longitude")
    lat_b = req_b.get("latitude")
    lon_b = req_b.get("longitude")

    # If coordinates are available on both
    if lat_a is not None and lon_a is not None and lat_b is not None and lon_b is not None:
        try:
            d_km = calculate_haversine_distance_km(float(lat_a), float(lon_a), float(lat_b), float(lon_b))
            if d_km <= max_distance_km:
                return True, f"Coordinates within {d_km:.1f} km"
            else:
                return False, f"Coordinates separated by {d_km:.1f} km (different localities)"
        except Exception:
            pass

    # If district IDs are present
    if dist_a and dist_b:
        if dist_a == dist_b:
            return True, "Identical district boundary"
        else:
            return False, "Different administrative districts"

    # If location names match closely
    loc_a = (req_a.get("location_name") or "").strip().lower()
    loc_b = (req_b.get("location_name") or "").strip().lower()
    if loc_a and loc_b and loc_a == loc_b and loc_a not in ("location unspecified", "unknown"):
        return True, f"Identical location name '{loc_a}'"

    # Default: if location is unknown, assume same if district is not explicitly different
    return True, "Co-located or district unconstrained"


def classify_relationship(
    req_a: Dict[str, Any],
    req_b: Dict[str, Any],
    similarity_score: float,
    duplicate_threshold: Optional[float] = None,
    similarity_threshold: Optional[float] = None
) -> Tuple[str, str]:
    """
    Classifies the relationship between two requests into:
    - 'duplicate': Highly similar meaning (>= duplicate_threshold) AND verified co-location.
    - 'similar': Similar civic need (>= similarity_threshold) or high semantic similarity across different districts.
    - 'related': Moderate similarity (0.60 to similarity_threshold).

    Returns (relationship_type, explanation_reason).
    """
    dup_thresh = duplicate_threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD
    sim_thresh = similarity_threshold or settings.SIMILARITY_THRESHOLD

    co_located, loc_reason = are_locations_coincident(req_a, req_b)

    if similarity_score >= dup_thresh:
        if co_located:
            return (
                "duplicate",
                f"High semantic similarity ({similarity_score:.2f} >= {dup_thresh:.2f}) and coincident geography ({loc_reason})."
            )
        else:
            return (
                "similar",
                f"High semantic similarity ({similarity_score:.2f} >= {dup_thresh:.2f}) but separated geography ({loc_reason}); classified as similar rather than duplicate."
            )

    if similarity_score >= sim_thresh:
        return (
            "similar",
            f"Moderate-to-high semantic similarity ({similarity_score:.2f} >= {sim_thresh:.2f}) addressing {req_a.get('category', 'civic')} infrastructure."
        )

    if similarity_score >= 0.60:
        return (
            "related",
            f"Thematically related civic demand ({similarity_score:.2f})."
        )

    return ("none", f"Similarity {similarity_score:.2f} below threshold.")


def find_duplicates_for_request(
    target_request: Dict[str, Any],
    nearest_candidates: List[Dict[str, Any]],
    duplicate_threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Filters nearest neighbor candidates for true duplicates based on similarity and locality.
    """
    dup_thresh = duplicate_threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD
    duplicates = []

    for item in nearest_candidates:
        cand_record = item.get("record") or item
        sim = item["similarity_score"]
        rel_type, reason = classify_relationship(
            target_request,
            cand_record,
            sim,
            duplicate_threshold=dup_thresh
        )
        if rel_type == "duplicate":
            duplicates.append({
                "request_id": item["request_id"],
                "similarity_score": sim,
                "category": item.get("category"),
                "sub_category": item.get("sub_category"),
                "district_id": item.get("district_id"),
                "relationship_type": "duplicate",
                "explanation": reason,
                "created_at": item.get("created_at")
            })

    return duplicates
