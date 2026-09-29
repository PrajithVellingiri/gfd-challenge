"""
AI Analysis Endpoints for Multimodal Intelligence (Phase 4).
Handles automated request understanding, translation, categorization,
urgency assessment, speech-to-text, and visual inspection.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Header, status
from pydantic import BaseModel, Field

from app.db import (
    fetch_citizen_request,
    fetch_ai_analysis,
    upsert_ai_analysis
)
from app.services.ai.request_analyzer import default_request_analyzer
from app.services.ai.validators import (
    AIRequestAnalysisResponse,
    TextAnalysisResult
)

router = APIRouter(tags=["AI Intelligence"])


class DirectTextAnalyzePayload(BaseModel):
    text: str = Field(..., min_length=3, description="Citizen grievance or civic request text")


@router.post(
    "/api/requests/{request_id}/analyze",
    response_model=AIRequestAnalysisResponse,
    summary="Trigger Multimodal AI Analysis for a citizen request"
)
@router.post(
    "/api/v1/requests/{request_id}/analyze",
    response_model=AIRequestAnalysisResponse,
    summary="Trigger Multimodal AI Analysis (Phase 1 compat)"
)
async def analyze_request(
    request_id: UUID,
    user_id: Optional[UUID] = Query(None, description="Requesting Citizen User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID Header")
):
    """
    Executes multimodal AI intelligence on a citizen request.
    Extracts detected language, English translation, canonical category,
    sub-category, urgency, summary, keywords, speech transcription, and visual observations.
    """
    req_id_str = str(request_id)
    record = fetch_citizen_request(req_id_str)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citizen request '{request_id}' not found."
        )

    # Ownership check
    caller = user_id or x_user_id
    record_owner = record.get("user_id")
    if caller and record_owner and str(caller) != str(record_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not have permission to analyze this request."
        )

    # Execute Multimodal Analysis
    description = record.get("description")
    title = record.get("title")
    image_path = record.get("image_url")
    audio_path = record.get("audio_url")

    analysis_dict = default_request_analyzer.analyze_citizen_request(
        request_id=req_id_str,
        description=description,
        title=title,
        image_path=image_path,
        audio_path=audio_path
    )

    # Persist in DB
    saved_record = upsert_ai_analysis(analysis_dict)
    response_data = saved_record if saved_record else analysis_dict

    return AIRequestAnalysisResponse(**response_data)


@router.get(
    "/api/requests/{request_id}/analysis",
    response_model=AIRequestAnalysisResponse,
    summary="Get existing Multimodal AI Analysis for a citizen request"
)
@router.get(
    "/api/v1/requests/{request_id}/analysis",
    response_model=AIRequestAnalysisResponse,
    summary="Get existing Multimodal AI Analysis (Phase 1 compat)"
)
async def get_request_analysis(
    request_id: UUID,
    user_id: Optional[UUID] = Query(None, description="Requesting Citizen User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID Header")
):
    """
    Retrieves the stored AI analysis for a citizen request.
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
            detail="Unauthorized: You do not have permission to view analysis for this request."
        )

    analysis = fetch_ai_analysis(req_id_str)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI analysis has not been performed for this request yet."
        )

    return AIRequestAnalysisResponse(**analysis)


@router.post(
    "/api/ai/analyze-text",
    response_model=TextAnalysisResult,
    summary="Live preview text analysis via Gemini"
)
async def analyze_raw_text(payload: DirectTextAnalyzePayload):
    """
    Directly analyzes raw text grievance for live frontend preview or interactive triage.
    """
    try:
        return default_request_analyzer.analyze_text(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(exc)}"
        )
