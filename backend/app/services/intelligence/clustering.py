"""
District-Aware & Category-Aware Semantic Clustering Service (Phase 5).
Uses DBSCAN on pairwise cosine distance matrices with deterministic, explainable label synthesis.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from uuid import uuid4
import numpy as np
from sklearn.cluster import DBSCAN

from app.config import settings
from app.services.intelligence.similarity import compute_pairwise_cosine_distances


def synthesize_cluster_label(
    category: str,
    member_records: List[Dict[str, Any]]
) -> Tuple[str, str]:
    """
    Synthesizes a human-readable cluster label and summary deterministically
    from member sub-categories, summaries, and keywords without invoking external LLMs.
    """
    sub_cats = []
    keywords = []
    summaries = []

    for rec in member_records:
        sc = rec.get("sub_category")
        if sc and sc.strip() and sc.strip().lower() not in ("other", "none", "unknown"):
            sub_cats.append(sc.strip())

        kws = rec.get("keywords")
        if isinstance(kws, list):
            keywords.extend([str(k).strip() for k in kws if str(k).strip()])

        summ = rec.get("summary")
        if summ and summ.strip():
            summaries.append(summ.strip())

    # 1. Primary label: Most frequent sub-category
    if sub_cats:
        top_sc, _ = Counter(sub_cats).most_common(1)[0]
        label = top_sc
    elif keywords:
        top_kws = [k for k, _ in Counter(keywords).most_common(2)]
        label = f"{category}: {' & '.join(top_kws).title()}"
    else:
        label = f"{category} Demands Group"

    # 2. Executive summary for cluster
    count = len(member_records)
    if summaries:
        top_summary = summaries[0]
        if len(top_summary) > 120:
            top_summary = top_summary[:117] + "..."
        cluster_summary = f"Cluster of {count} civic requests: {top_summary}"
    else:
        cluster_summary = f"Cluster of {count} semantically related {category} requests."

    return label, cluster_summary


class RequestClusterer:
    """
    Semantic clustering engine for citizen grievances.
    Enforces district and category boundaries to prevent unrealistic cross-domain merging.
    """

    def __init__(
        self,
        eps: Optional[float] = None,
        min_samples: Optional[int] = None
    ):
        self.eps = eps or settings.CLUSTER_EPS
        self.min_samples = min_samples or settings.CLUSTER_MIN_SAMPLES

    def cluster_requests(
        self,
        request_records: List[Dict[str, Any]],
        district_id_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes district-aware and category-aware semantic clustering.
        Returns a list of cluster dictionaries with member references.
        """
        if not request_records:
            return []

        # 1. Partition requests by (district_id, category)
        partitions: Dict[Tuple[Optional[str], str], List[Dict[str, Any]]] = {}
        for req in request_records:
            d_id = str(req.get("district_id")) if req.get("district_id") else None
            cat = str(req.get("category") or "Other").strip().capitalize()

            if district_id_filter and str(district_id_filter) != str(d_id):
                continue
            if category_filter and category_filter.lower() != cat.lower():
                continue

            # Request must have a valid embedding
            if not req.get("embedding"):
                continue

            key = (d_id, cat)
            partitions.setdefault(key, []).append(req)

        formed_clusters = []

        # 2. Run DBSCAN on each partition independently
        for (dist_id, cat), group_reqs in partitions.items():
            if len(group_reqs) < self.min_samples:
                continue

            vectors = [r["embedding"] for r in group_reqs]
            dist_matrix = compute_pairwise_cosine_distances(vectors)

            # Fit DBSCAN
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="precomputed")
            labels = db.fit_predict(dist_matrix)

            # Group requests by assigned cluster label
            clusters_by_label: Dict[int, List[Dict[str, Any]]] = {}
            for idx, cluster_idx in enumerate(labels):
                if cluster_idx == -1:
                    # Noise / outlier
                    continue
                clusters_by_label.setdefault(cluster_idx, []).append(group_reqs[idx])

            for cluster_idx, members in clusters_by_label.items():
                cluster_label, summary = synthesize_cluster_label(cat, members)
                cluster_id = str(uuid4())

                formed_clusters.append({
                    "id": cluster_id,
                    "cluster_label": cluster_label,
                    "category": cat,
                    "district_id": dist_id,
                    "request_count": len(members),
                    "summary": summary,
                    "member_requests": [
                        {
                            "request_id": str(m["request_id"]),
                            "similarity_score": round(1.0 - float(dist_matrix[group_reqs.index(m), group_reqs.index(members[0])]), 4) if len(members) > 1 else 1.0,
                            "category": m.get("category"),
                            "sub_category": m.get("sub_category"),
                            "created_at": m.get("created_at")
                        }
                        for m in members
                    ]
                })

        # Sort clusters by request count descending
        formed_clusters.sort(key=lambda c: c["request_count"], reverse=True)
        return formed_clusters
