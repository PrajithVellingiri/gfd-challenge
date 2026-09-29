"""
Vector Similarity & Nearest Neighbor Search Operations (Phase 5).
"""

from typing import List, Dict, Any, Tuple
import numpy as np


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two numeric vectors.
    Returns float in range [-1.0, 1.0].
    """
    if not vec_a or not vec_b:
        return 0.0
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = float(np.dot(a, b) / (norm_a * norm_b))
    return max(-1.0, min(1.0, sim))


def cosine_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine distance (1 - cosine_similarity).
    Distance in range [0.0, 2.0].
    """
    return max(0.0, 1.0 - cosine_similarity(vec_a, vec_b))


def compute_pairwise_cosine_distances(vectors: List[List[float]]) -> np.ndarray:
    """
    Computes symmetric NxN pairwise cosine distance matrix for clustering.
    """
    mat = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    normalized = mat / norms
    sim_matrix = np.dot(normalized, normalized.T)
    # Cosine distance = 1 - cosine similarity
    dist_matrix = np.clip(1.0 - sim_matrix, 0.0, 2.0)
    return dist_matrix


def rank_nearest_neighbors(
    query_vector: List[float],
    candidate_records: List[Dict[str, Any]],
    top_k: int = 10,
    min_threshold: float = 0.75,
    exclude_request_id: Any = None
) -> List[Dict[str, Any]]:
    """
    Ranks candidate embedding records against query vector.
    Returns sorted list of top_k matches above min_threshold.
    """
    if not query_vector or not candidate_records:
        return []

    scored_candidates = []
    q_vec = np.asarray(query_vector, dtype=np.float32)
    q_norm = np.linalg.norm(q_vec)
    if q_norm == 0:
        return []

    for item in candidate_records:
        req_id = item.get("request_id")
        if exclude_request_id and str(req_id) == str(exclude_request_id):
            continue

        cand_vec = item.get("embedding")
        if not cand_vec:
            continue

        c_vec = np.asarray(cand_vec, dtype=np.float32)
        c_norm = np.linalg.norm(c_vec)
        if c_norm == 0:
            continue

        sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
        sim = max(-1.0, min(1.0, sim))

        if sim >= min_threshold:
            scored_candidates.append({
                "request_id": str(req_id),
                "similarity_score": round(sim, 4),
                "category": item.get("category"),
                "sub_category": item.get("sub_category"),
                "district_id": str(item.get("district_id")) if item.get("district_id") else None,
                "created_at": item.get("created_at"),
                "record": item
            })

    scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_candidates[:top_k]
