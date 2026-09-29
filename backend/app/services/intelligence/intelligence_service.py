"""
Master Request Intelligence Service (Phase 5).
Coordinates semantic embedding generation, vector similarity search,
duplicate detection, district-aware clustering, and emerging issue detection.
"""

from typing import List, Dict, Any, Optional
import logging
from app.config import settings
from app.db import (
    fetch_citizen_request,
    fetch_ai_analysis,
    save_request_embedding,
    fetch_request_embedding,
    list_request_embeddings_with_meta,
    save_request_similarity,
    fetch_request_similarities,
    save_clusters,
    fetch_clusters,
    save_emerging_issues,
    fetch_emerging_issues,
    list_citizen_requests,
)
from app.services.intelligence.embeddings import (
    get_embedding_provider,
    extract_request_text_for_embedding,
    EmbeddingProvider
)
from app.services.intelligence.similarity import rank_nearest_neighbors
from app.services.intelligence.duplicate_detector import (
    classify_relationship,
    find_duplicates_for_request
)
from app.services.intelligence.clustering import RequestClusterer
from app.services.intelligence.emerging_issues import EmergingIssueDetector

logger = logging.getLogger(__name__)


class IntelligenceService:
    """
    Unified intelligence facade for DPI citizen requests.
    Transforms individual requests into relational intelligence.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        clusterer: Optional[RequestClusterer] = None,
        emerging_detector: Optional[EmergingIssueDetector] = None
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.clusterer = clusterer or RequestClusterer()
        self.emerging_detector = emerging_detector or EmergingIssueDetector()

    def generate_embedding(
        self,
        request_id: str,
        text_override: Optional[str] = None
    ) -> List[float]:
        """
        Generates and persists 768-dim semantic embedding for a citizen request.
        """
        req_id = str(request_id)
        if text_override:
            clean_text = text_override
        else:
            req_data = fetch_citizen_request(req_id) or {}
            ai_data = fetch_ai_analysis(req_id)
            clean_text = extract_request_text_for_embedding(req_data, ai_data)

        vec = self.embedding_provider.embed_text(clean_text)
        save_request_embedding(
            request_id=req_id,
            embedding=vec,
            model_name=settings.EMBEDDING_MODEL,
            version="v1.0"
        )
        return vec

    def find_similar_requests(
        self,
        request_id: str,
        top_k: Optional[int] = None,
        min_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds semantically similar requests using vector nearest-neighbor search.
        Enforces anonymization (never returns private citizen personal identifiers).
        """
        req_id = str(request_id)
        k = top_k or settings.TOP_K_SIMILAR_REQUESTS
        thresh = min_threshold or settings.SIMILARITY_THRESHOLD

        # 1. Fetch or generate target embedding
        query_vec = fetch_request_embedding(req_id)
        if not query_vec:
            query_vec = self.generate_embedding(req_id)

        target_req = fetch_citizen_request(req_id) or {"id": req_id}

        # 2. Retrieve candidate embeddings
        candidates = list_request_embeddings_with_meta(limit=1000)

        # 3. Rank nearest neighbors
        nearest = rank_nearest_neighbors(
            query_vector=query_vec,
            candidate_records=candidates,
            top_k=k,
            min_threshold=thresh,
            exclude_request_id=req_id
        )

        results = []
        for match in nearest:
            cand_rec = match.get("record") or match
            sim = match["similarity_score"]
            rel_type, reason = classify_relationship(target_req, cand_rec, sim)

            # Persist relationship in DB
            save_request_similarity(
                source_request_id=req_id,
                target_request_id=match["request_id"],
                similarity_score=sim,
                relationship_type=rel_type if rel_type != "none" else "related"
            )

            # Privacy-safe anonymized representation
            results.append({
                "request_id": match["request_id"],
                "similarity_score": sim,
                "category": match.get("category"),
                "sub_category": match.get("sub_category"),
                "district_id": match.get("district_id"),
                "relationship_type": rel_type if rel_type != "none" else "similar",
                "explanation": reason,
                "created_at": match.get("created_at")
            })

        return results

    def detect_duplicates(
        self,
        request_id: str,
        duplicate_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters similar requests for true duplicates based on high similarity and geographic co-location.
        """
        req_id = str(request_id)
        thresh = duplicate_threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD
        similar_items = self.find_similar_requests(req_id, top_k=20, min_threshold=0.70)

        target_req = fetch_citizen_request(req_id) or {"id": req_id}
        duplicates = find_duplicates_for_request(
            target_request=target_req,
            nearest_candidates=similar_items,
            duplicate_threshold=thresh
        )
        return duplicates

    def cluster_requests(
        self,
        district_id: Optional[str] = None,
        category: Optional[str] = None,
        eps: Optional[float] = None,
        min_samples: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes district-aware and category-aware semantic clustering.
        """
        candidates = list_request_embeddings_with_meta(limit=2000)

        clusterer = RequestClusterer(
            eps=eps or settings.CLUSTER_EPS,
            min_samples=min_samples or settings.CLUSTER_MIN_SAMPLES
        )
        clusters = clusterer.cluster_requests(
            request_records=candidates,
            district_id_filter=district_id,
            category_filter=category
        )

        save_clusters(clusters)
        return clusters

    def detect_emerging_issues(
        self,
        district_id: Optional[str] = None,
        category: Optional[str] = None,
        window_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Scans requests and detects emerging surge signals.
        """
        all_requests = list_citizen_requests(limit=5000)
        detector = EmergingIssueDetector(window_days=window_days)
        issues = detector.detect_emerging_issues(
            requests=all_requests,
            district_id_filter=district_id,
            category_filter=category
        )
        save_emerging_issues(issues)
        return issues

    def process_pending_intelligence(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Batch processing job:
        1. Embeds un-embedded requests.
        2. Calculates similarities for updated requests.
        3. Refreshes clusters.
        4. Detects emerging issues.
        """
        requests = list_citizen_requests(limit=batch_size)
        embedded_count = 0
        similarity_count = 0

        for r in requests:
            rid = str(r["id"])
            existing_vec = fetch_request_embedding(rid)
            if not existing_vec:
                try:
                    self.generate_embedding(rid)
                    embedded_count += 1
                except Exception as exc:
                    logger.warning("Failed to generate embedding for request %s: %s", rid, exc)

        # Run similarity search for newly embedded requests
        for r in requests[:20]:
            rid = str(r["id"])
            try:
                sims = self.find_similar_requests(rid, top_k=5)
                similarity_count += len(sims)
            except Exception:
                pass

        # Refresh clusters and emerging issues
        clusters = self.cluster_requests()
        emerging = self.detect_emerging_issues()

        return {
            "success": True,
            "embeddings_generated": embedded_count,
            "similarities_recorded": similarity_count,
            "clusters_count": len(clusters),
            "emerging_issues_count": len(emerging)
        }


# Default global instance
default_intelligence_service = IntelligenceService()
