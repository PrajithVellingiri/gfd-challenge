"""
FastAPI Router for Request Intelligence (Phase 5).
Exposes endpoints for similar requests, duplicate groups, semantic clusters,
emerging issue signals, and batch processing.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Header, Depends, status
from pydantic import BaseModel, Field

from app.db import fetch_citizen_request, fetch_clusters
from app.services.intelligence.intelligence_service import default_intelligence_service
from app.services.auth_dependencies import verify_admin_authorization

router = APIRouter(tags=["Request Intelligence"])


# Pydantic Response Models
class SimilarRequestItem(BaseModel):
    request_id: str
    similarity_score: float
    category: Optional[str] = None
    sub_category: Optional[str] = None
    district_id: Optional[str] = None
    relationship_type: str = "similar"
    explanation: Optional[str] = None
    created_at: Optional[str] = None


class DuplicateGroupItem(BaseModel):
    request_id: str
    similarity_score: float
    category: Optional[str] = None
    sub_category: Optional[str] = None
    district_id: Optional[str] = None
    relationship_type: str = "duplicate"
    explanation: str
    created_at: Optional[str] = None


class ClusterItem(BaseModel):
    id: str
    cluster_label: str
    category: str
    district_id: Optional[str] = None
    request_count: int
    summary: Optional[str] = None
    created_at: Optional[str] = None


class EmergingIssueItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    sub_category: Optional[str] = None
    district_id: Optional[str] = None
    current_count: int
    previous_count: int
    growth_percentage: Optional[float] = None
    indicator: str
    signal_type: str = "AI/data-derived signal (advisory governance triage)"


class BatchProcessResponse(BaseModel):
    success: bool
    embeddings_generated: int
    similarities_recorded: int
    clusters_count: int
    emerging_issues_count: int


@router.get(
    "/api/requests/{request_id}/similar",
    response_model=List[SimilarRequestItem],
    summary="Get semantically similar requests"
)
@router.get(
    "/api/v1/requests/{request_id}/similar",
    response_model=List[SimilarRequestItem],
    summary="Get semantically similar requests (Phase 1 compat)"
)
async def get_similar_requests(
    request_id: UUID,
    top_k: int = Query(10, ge=1, le=50, description="Maximum similar requests to return"),
    min_threshold: float = Query(0.70, ge=0.0, le=1.0, description="Minimum cosine similarity threshold"),
    user_id: Optional[UUID] = Query(None, description="Requesting Citizen User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID Header")
):
    """
    Retrieves semantically similar requests via vector cosine similarity.
    Enforces privacy by returning only anonymized civic metrics.
    """
    req_id_str = str(request_id)
    record = fetch_citizen_request(req_id_str)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citizen request '{request_id}' not found."
        )

    # Ownership check: citizen can query similarity for their own request
    caller = user_id or x_user_id
    record_owner = record.get("user_id")
    if caller and record_owner and str(caller) != str(record_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not have permission to view intelligence for this request."
        )

    similar_items = default_intelligence_service.find_similar_requests(
        request_id=req_id_str,
        top_k=top_k,
        min_threshold=min_threshold
    )
    return [SimilarRequestItem(**item) for item in similar_items]


@router.get(
    "/api/requests/{request_id}/duplicates",
    response_model=List[DuplicateGroupItem],
    summary="Get duplicate or near-duplicate requests"
)
@router.get(
    "/api/v1/requests/{request_id}/duplicates",
    response_model=List[DuplicateGroupItem],
    summary="Get duplicate requests (Phase 1 compat)"
)
async def get_duplicate_requests(
    request_id: UUID,
    threshold: Optional[float] = Query(None, ge=0.5, le=1.0, description="Duplicate cosine similarity threshold"),
    user_id: Optional[UUID] = Query(None, description="Requesting Citizen User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID Header")
):
    """
    Detects potential duplicate and near-duplicate requests matching meaning and geographic location.
    """
    req_id_str = str(request_id)
    record = fetch_citizen_request(req_id_str)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citizen request '{request_id}' not found."
        )

    caller = user_id or x_user_id
    record_owner = record.get("user_id")
    if caller and record_owner and str(caller) != str(record_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not have permission to inspect duplicates for this request."
        )

    duplicates = default_intelligence_service.detect_duplicates(
        request_id=req_id_str,
        duplicate_threshold=threshold
    )
    return [DuplicateGroupItem(**d) for d in duplicates]


@router.post(
    "/api/requests/{request_id}/intelligence",
    summary="Explicitly trigger intelligence processing for a request"
)
async def trigger_request_intelligence(
    request_id: UUID,
    user_id: Optional[UUID] = Query(None, description="Requesting Citizen User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID Header")
):
    """
    Generates embedding and identifies nearest neighbors for a single citizen request.
    """
    req_id_str = str(request_id)
    record = fetch_citizen_request(req_id_str)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citizen request '{request_id}' not found."
        )

    caller = user_id or x_user_id
    record_owner = record.get("user_id")
    if caller and record_owner and str(caller) != str(record_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not have permission to trigger intelligence for this request."
        )

    # 1. Generate embedding
    vec = default_intelligence_service.generate_embedding(req_id_str)
    # 2. Find similar requests
    similar = default_intelligence_service.find_similar_requests(req_id_str)
    # 3. Find duplicates
    duplicates = default_intelligence_service.detect_duplicates(req_id_str)

    return {
        "success": True,
        "request_id": req_id_str,
        "embedding_dimension": len(vec),
        "similar_count": len(similar),
        "duplicates_count": len(duplicates),
        "duplicates": duplicates
    }


@router.get(
    "/api/intelligence/clusters",
    response_model=List[ClusterItem],
    summary="List semantic request clusters"
)
async def get_clusters(
    district_id: Optional[str] = Query(None, description="Filter clusters by district UUID"),
    category: Optional[str] = Query(None, description="Filter clusters by category")
):
    """
    Lists aggregated semantic clusters grouped by district and infrastructure category.
    """
    clusters = fetch_clusters(district_id=district_id, category=category)
    if not clusters:
        # Generate clusters if none persisted
        clusters = default_intelligence_service.cluster_requests(
            district_id=district_id,
            category=category
        )
    return [ClusterItem(**c) for c in clusters]


@router.get(
    "/api/intelligence/clusters/{cluster_id}",
    response_model=ClusterItem,
    summary="Get single cluster details"
)
async def get_cluster_by_id(cluster_id: str):
    """
    Retrieves details for a single cluster.
    """
    all_clusters = fetch_clusters()
    match = next((c for c in all_clusters if str(c.get("id")) == str(cluster_id)), None)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found.")
    return ClusterItem(**match)


@router.get(
    "/api/intelligence/emerging-issues",
    response_model=List[EmergingIssueItem],
    summary="List emerging civic demand surges"
)
async def get_emerging_issues(
    district_id: Optional[str] = Query(None, description="Filter by district UUID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    window_days: int = Query(7, ge=1, le=90, description="Observation window in days")
):
    """
    Lists accelerating citizen grievance trends comparing recent volume with previous periods.
    """
    issues = default_intelligence_service.detect_emerging_issues(
        district_id=district_id,
        category=category,
        window_days=window_days
    )
    return [EmergingIssueItem(**iss) for iss in issues]


@router.post(
    "/api/intelligence/process-pending",
    response_model=BatchProcessResponse,
    summary="Batch process pending requests for embeddings, similarities, and clusters"
)
async def process_pending_intelligence_batch(
    batch_size: int = Query(50, ge=1, le=500, description="Number of requests to process in batch"),
    authorized: bool = Depends(verify_admin_authorization)
):
    """
    Batch administrative job to embed, calculate similarities, and refresh clusters.
    Requires administrator credentials in production.
    """
    res = default_intelligence_service.process_pending_intelligence(batch_size=batch_size)
    return BatchProcessResponse(**res)
