"""
Request Intelligence Package (Phase 5).
Exposes embedding generation, vector similarity, duplicate detection,
semantic clustering, and emerging issue detection.
"""

from .embeddings import get_embedding_provider, EmbeddingProvider, GeminiEmbeddingProvider, MockEmbeddingProvider
from .similarity import cosine_similarity, cosine_distance, rank_nearest_neighbors
from .duplicate_detector import classify_relationship, find_duplicates_for_request
from .clustering import RequestClusterer
from .emerging_issues import EmergingIssueDetector
from .intelligence_service import IntelligenceService, default_intelligence_service

__all__ = [
    "get_embedding_provider",
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "MockEmbeddingProvider",
    "cosine_similarity",
    "cosine_distance",
    "rank_nearest_neighbors",
    "classify_relationship",
    "find_duplicates_for_request",
    "RequestClusterer",
    "EmergingIssueDetector",
    "IntelligenceService",
    "default_intelligence_service",
]
