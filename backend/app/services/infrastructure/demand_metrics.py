"""
Citizen Demand Metrics Aggregator (Phase 6).
Computes district demand metrics, 7-day volume trends, sector breakdowns,
cluster shares, and population-normalized request rates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from app.services.infrastructure.metrics import calculate_population_ratio


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parses timestamp into UTC datetime."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        clean = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def calculate_district_demand_metrics(
    requests: List[Dict[str, Any]],
    population: Optional[int],
    reference_time: Optional[datetime] = None,
    clusters: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes comprehensive citizen demand metrics for a single district.
    """
    if not requests:
        return {
            "total_requests": 0,
            "requests_last_7_days": 0,
            "requests_previous_7_days": 0,
            "request_growth_percentage": None,
            "requests_per_10000": None,
            "requests_by_sector": {},
            "cluster_metrics": {
                "cluster_count": 0,
                "largest_cluster_size": 0,
                "top_cluster": None,
                "top_cluster_percentage": 0.0,
                "emerging_cluster_count": 0
            }
        }

    # 1. Total & Sector breakdown
    total_reqs = len(requests)
    by_sector: Dict[str, int] = {}
    timestamps: List[datetime] = []

    for r in requests:
        cat = (r.get("category") or "other").strip().lower()
        by_sector[cat] = by_sector.get(cat, 0) + 1

        dt = parse_timestamp(r.get("created_at"))
        if dt:
            timestamps.append(dt)

    # 2. Window-based growth (last 7 days vs previous 7 days)
    t_end = reference_time or (max(timestamps) if timestamps else datetime.now(timezone.utc))
    t_mid = t_end - timedelta(days=7)
    t_start = t_mid - timedelta(days=7)

    recent_7d = sum(1 for t in timestamps if t_mid <= t <= t_end)
    prev_7d = sum(1 for t in timestamps if t_start <= t < t_mid)

    growth_pct: Optional[float] = None
    if prev_7d > 0:
        growth_pct = round(((recent_7d - prev_7d) / prev_7d) * 100.0, 1)
    else:
        growth_pct = None  # None if previous was zero; do not invent fake 100%

    # 3. Population-normalized demand
    per_10k = calculate_population_ratio(total_reqs, population, 10000.0)

    # 4. Cluster metrics (from Phase 5 clusters)
    cluster_metrics = {
        "cluster_count": 0,
        "largest_cluster_size": 0,
        "top_cluster": None,
        "top_cluster_percentage": 0.0,
        "emerging_cluster_count": 0
    }

    if clusters:
        cluster_metrics["cluster_count"] = len(clusters)
        sorted_clusters = sorted(clusters, key=lambda c: c.get("request_count", 0), reverse=True)
        if sorted_clusters:
            top_c = sorted_clusters[0]
            top_size = top_c.get("request_count", 0)
            cluster_metrics["largest_cluster_size"] = top_size
            cluster_metrics["top_cluster"] = top_c.get("cluster_label")
            if total_reqs > 0:
                cluster_metrics["top_cluster_percentage"] = round((top_size / float(total_reqs)) * 100.0, 1)

    return {
        "total_requests": total_reqs,
        "requests_last_7_days": recent_7d,
        "requests_previous_7_days": prev_7d,
        "request_growth_percentage": growth_pct,
        "requests_per_10000": per_10k,
        "requests_by_sector": by_sector,
        "cluster_metrics": cluster_metrics
    }
