"""
Semantic Embedding Service for Request Intelligence (Phase 5).
Provides provider-agnostic embeddings (Gemini text-embedding-004, local models, or deterministic mock)
producing 768-dimensional normalized vectors compatible with PostgreSQL pgvector.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import hashlib
import logging
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates a 768-dimensional embedding for a single text string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        pass


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini Embedding Provider using models/text-embedding-004.
    Produces 768-dimensional semantic embeddings.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL or "models/text-embedding-004"
        self._configured = False

    def _ensure_configured(self):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in backend environment.")
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    def embed_text(self, text: str) -> List[float]:
        self._ensure_configured()
        import google.generativeai as genai
        clean_text = text.strip() if text else ""
        if not clean_text:
            return [0.0] * settings.EMBEDDING_DIMENSION

        try:
            result = genai.embed_content(
                model=self.model,
                content=clean_text,
                task_type="clustering"
            )
            embedding = result.get("embedding", [])
            # If embedding exceeds or is less than target dimension, adjust safely
            if len(embedding) > settings.EMBEDDING_DIMENSION:
                embedding = embedding[:settings.EMBEDDING_DIMENSION]
            elif len(embedding) < settings.EMBEDDING_DIMENSION:
                embedding.extend([0.0] * (settings.EMBEDDING_DIMENSION - len(embedding)))
            return embedding
        except Exception as exc:
            logger.error("Gemini embed_content failed: %s", exc)
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline embedding provider for test environments.
    Uses SHA-256 token hashing and random projection to generate unit-normalized 768-dim vectors.
    Produces identical vectors for identical texts and high similarity for overlapping vocabulary.
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        clean = (text or "").lower().strip()
        if not clean:
            return [0.0] * self.dimension

        # Generate a base vector from tokens
        tokens = [t for t in clean.replace(".", " ").replace(",", " ").split() if t]
        vec = np.zeros(self.dimension, dtype=np.float32)

        for token in tokens:
            seed = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            token_vec = rng.randn(self.dimension)
            vec += token_vec

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def extract_request_text_for_embedding(request: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None) -> str:
    """
    Extracts canonical semantic text representation from a request and its Phase 4 AI analysis.
    Prioritizes English translation and summary to guarantee cross-lingual semantic alignment.
    """
    parts = []
    if analysis:
        if analysis.get("translated_text"):
            parts.append(analysis["translated_text"].strip())
        elif analysis.get("summary"):
            parts.append(analysis["summary"].strip())
        if analysis.get("category"):
            parts.append(f"Category: {analysis['category']}")
        if analysis.get("sub_category"):
            parts.append(f"Sub-category: {analysis['sub_category']}")
        if analysis.get("keywords") and isinstance(analysis["keywords"], list):
            parts.append("Keywords: " + ", ".join(analysis["keywords"]))

    if not parts:
        desc = request.get("description", "")
        title = request.get("title", "")
        if title:
            parts.append(title.strip())
        if desc:
            parts.append(desc.strip())

    return " | ".join(parts) if parts else "Civic grievance"


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """Factory to retrieve configured embedding provider."""
    p = (provider_type or settings.EMBEDDING_PROVIDER or "gemini").lower()
    if p == "mock":
        return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
    elif p == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.info("GEMINI_API_KEY not configured, falling back to deterministic mock embedding provider.")
            return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
        return GeminiEmbeddingProvider()
    return MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
