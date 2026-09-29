from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query, status

from app.db import (
    insert_citizen_request,
    fetch_citizen_request,
    list_citizen_requests
)
from app.models.schemas import (
    CitizenRequestCreate,
    CitizenRequestResponse,
    StoragePathGenerateRequest,
    StoragePathGenerateResponse,
)
from app.services.storage import storage_service

router = APIRouter(prefix="/api/v1/requests", tags=["Citizen Requests"])


@router.post(
    "",
    response_model=CitizenRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a basic citizen request"
)
async def create_request(payload: CitizenRequestCreate):
    """
    Submits a new citizen request. Stores only storage path references for images/audio.
    Never stores binary file data directly in the database.
    """
    # Validate storage path ownership if image_path or audio_path provided
    if payload.user_id:
        if payload.image_path and not storage_service.validate_storage_path_owner(payload.image_path, payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_path does not conform to the authenticated user directory."
            )
        if payload.audio_path and not storage_service.validate_storage_path_owner(payload.audio_path, payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="audio_path does not conform to the authenticated user directory."
            )

    req_data = payload.model_dump(exclude_unset=True)
    if "user_id" in req_data and req_data["user_id"]:
        req_data["user_id"] = str(req_data["user_id"])
    if "urgency" in req_data:
        req_data["urgency"] = req_data["urgency"].value

    inserted = insert_citizen_request(req_data)
    if not inserted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record citizen request in database."
        )

    return inserted


@router.get(
    "/{request_id}",
    response_model=CitizenRequestResponse,
    summary="Get citizen request details by ID"
)
async def get_request(request_id: UUID):
    """
    Retrieves a citizen request by its unique UUID.
    """
    record = fetch_citizen_request(str(request_id))
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen request not found."
        )
    return record


@router.get(
    "",
    response_model=List[CitizenRequestResponse],
    summary="List citizen requests"
)
async def list_requests(
    user_id: Optional[UUID] = Query(None, description="Filter requests by citizen user ID"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Lists citizen requests with pagination and optional user filter.
    """
    records = list_citizen_requests(
        user_id=str(user_id) if user_id else None,
        limit=limit,
        offset=offset
    )
    return records


@router.post(
    "/storage-path",
    response_model=StoragePathGenerateResponse,
    summary="Generate isolated Supabase Storage path for media upload"
)
async def generate_upload_path(payload: StoragePathGenerateRequest):
    """
    Generates a secure user/request isolated storage path for uploading media to Supabase Storage.
    Path format: {user_id}/{request_id}/{sanitized_filename}
    """
    try:
        bucket_name = storage_service.get_bucket_for_type(payload.bucket_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    storage_path = storage_service.generate_storage_path(
        user_id=payload.user_id,
        request_id=payload.request_id,
        original_filename=payload.original_filename
    )

    if payload.bucket_type.lower() in ("image", "photo", "img"):
        allowed = storage_service.ALLOWED_IMAGE_MIMES
        max_size = storage_service.MAX_IMAGE_SIZE_BYTES
    else:
        allowed = storage_service.ALLOWED_AUDIO_MIMES
        max_size = storage_service.MAX_AUDIO_SIZE_BYTES

    return StoragePathGenerateResponse(
        bucket=bucket_name,
        storage_path=storage_path,
        allowed_mime_types=allowed,
        max_size_bytes=max_size
    )
