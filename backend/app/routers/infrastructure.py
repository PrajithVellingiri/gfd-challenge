"""
FastAPI Router for Infrastructure Intelligence & Gap Detection (Phase 6).
Provides decision-support signals connecting citizen demand with public infrastructure datasets.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field

from app.services.infrastructure.infrastructure_service import default_infrastructure_service
from app.services.auth_dependencies import verify_admin_authorization

router = APIRouter(tags=["Infrastructure Intelligence"])


class GapEvidenceModel(BaseModel):
    what_was_observed: Optional[str] = None
    infrastructure_observed: Optional[str] = None
    why_signal_generated: Optional[str] = None
    datasets_used: Optional[List[str]] = Field(default_factory=list)


class GapSignalModel(BaseModel):
    signal_type: str
    severity: str
    mismatch_state: str
    demand_percentile: Optional[float] = None
    infrastructure_percentile: Optional[float] = None
    gap_delta: Optional[float] = None
    summary: str
    evidence: Optional[GapEvidenceModel] = None


class DistrictIntelligenceItem(BaseModel):
    id: Optional[str] = None
    district_id: str
    district_name: Optional[str] = None
    state: Optional[str] = None
    sector: str
    population: Optional[int] = None
    population_source: Optional[str] = None
    total_requests: int
    requests_last_7_days: int
    requests_previous_7_days: int
    request_growth_percentage: Optional[float] = None
    requests_per_10000: Optional[float] = None
    demand_percentile: Optional[float] = None
    infrastructure_percentile: Optional[float] = None
    demand_metrics: Dict[str, Any] = Field(default_factory=dict)
    infrastructure_metrics: Dict[str, Any] = Field(default_factory=dict)
    health_metrics: Dict[str, Any] = Field(default_factory=dict)
    investment_metrics: Dict[str, Any] = Field(default_factory=dict)
    cluster_metrics: Dict[str, Any] = Field(default_factory=dict)
    mismatch_signal: str
    gap_signal: Dict[str, Any] = Field(default_factory=dict)
    data_sources: List[Dict[str, Any]] = Field(default_factory=list)
    computed_at: Optional[str] = None


class GapSignalListItem(BaseModel):
    district_id: str
    district_name: Optional[str] = None
    state: Optional[str] = None
    sector: str
    signal_type: str
    severity: str
    demand_percentile: Optional[float] = None
    infrastructure_percentile: Optional[float] = None
    summary: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[Dict[str, Any]]] = None


class RefreshResponse(BaseModel):
    success: bool
    districts_processed: int
    sectors_per_district: int
    total_records_generated: int
    potential_gaps_identified: int
    infrastructure_pressure_signals: int


@router.get(
    "/api/infrastructure/districts",
    response_model=List[DistrictIntelligenceItem],
    summary="List district infrastructure intelligence summaries"
)
async def list_district_intelligence(
    sector: Optional[str] = Query(None, description="Filter by sector (e.g. Healthcare, Water, Education, Roads, Overall)"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    mismatch_signal: Optional[str] = Query(None, description="Filter by signal type (e.g. potential_gap, infrastructure_pressure, balanced)")
):
    """
    Retrieves multidimensional district intelligence records comparing citizen demand
    with public infrastructure availability across sectors.
    """
    records = default_infrastructure_service.list_district_intelligence(
        sector=sector,
        state=state,
        mismatch_signal=mismatch_signal
    )
    return [DistrictIntelligenceItem(**r) for r in records]


@router.get(
    "/api/infrastructure/districts/{district_id}",
    response_model=List[DistrictIntelligenceItem],
    summary="Get infrastructure intelligence for a specific district across all sectors"
)
async def get_district_intelligence(
    district_id: UUID,
    sector: Optional[str] = Query(None, description="Optional sector filter")
):
    """
    Retrieves complete multi-sector intelligence for a single district.
    """
    records = default_infrastructure_service.get_district_intelligence(
        district_id=str(district_id),
        sector=sector
    )
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intelligence records for district '{district_id}' not found."
        )
    return [DistrictIntelligenceItem(**r) for r in records]


@router.get(
    "/api/infrastructure/districts/{district_id}/sectors",
    summary="Get available sector breakdown for a district"
)
async def get_district_sectors(district_id: UUID):
    """
    Returns high-level summary of all analyzed sectors for a district.
    """
    records = default_infrastructure_service.get_district_intelligence(str(district_id))
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_id}' not found."
        )

    summary_list = []
    for r in records:
        summary_list.append({
            "sector": r["sector"],
            "total_requests": r["total_requests"],
            "demand_percentile": r.get("demand_percentile"),
            "infrastructure_percentile": r.get("infrastructure_percentile"),
            "mismatch_signal": r.get("mismatch_signal"),
            "summary": (r.get("gap_signal") or {}).get("summary")
        })

    return {
        "district_id": str(district_id),
        "district_name": records[0].get("district_name"),
        "state": records[0].get("state"),
        "population": records[0].get("population"),
        "sectors": summary_list
    }


@router.get(
    "/api/infrastructure/gap-signals",
    response_model=List[GapSignalListItem],
    summary="List detected potential infrastructure gap and pressure signals"
)
async def list_gap_signals(
    sector: Optional[str] = Query(None, description="Filter signals by sector"),
    min_severity: Optional[str] = Query(None, description="Minimum severity: 'high' or 'medium'")
):
    """
    Retrieves decision-support gap signals where high citizen demand coincides
    with relatively low observed infrastructure availability.
    """
    signals = default_infrastructure_service.get_gap_signals(
        sector=sector,
        min_severity=min_severity
    )
    return [GapSignalListItem(**s) for s in signals]


@router.post(
    "/api/infrastructure/refresh",
    response_model=RefreshResponse,
    summary="Recompute all district intelligence and gap signals"
)
async def refresh_infrastructure_intelligence(
    authorized: bool = Depends(verify_admin_authorization)
):
    """
    Triggers deterministic recalculation of all district intelligence,
    cross-district relative percentiles, and gap signals.
    Requires administrator credentials in production.
    """
    res = default_infrastructure_service.refresh_all_intelligence()
    return RefreshResponse(**res)
