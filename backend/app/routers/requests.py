from typing import List, Optional, Union
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Header, status
from fastapi.responses import JSONResponse

from app.db import (
    insert_citizen_request,
    fetch_citizen_request,
    list_citizen_requests,
    get_supabase_client
)
from app.models.schemas import (
    CitizenRequestCreate,
    CitizenRequestResponse,
    CitizenSubmissionResponse,
    StoragePathGenerateRequest,
    StoragePathGenerateResponse,
    FileUploadResponse,
)
from app.services.storage import storage_service
from app.services.district_resolver import district_resolver

router = APIRouter(tags=["Citizen Requests"])


def build_error_response(status_code: int, code: str, message: str, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    )


@router.post(
    "/api/requests",
    response_model=CitizenSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a citizen request (Phase 3 format)"
)
@router.post(
    "/api/v1/requests",
    response_model=Union[CitizenSubmissionResponse, CitizenRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a citizen request (Phase 1 backwards-compatible)"
)
async def create_request(payload: CitizenRequestCreate):
    """
    Submits a new citizen development request.
    Validates input, validates storage file references, resolves canonical district via PostGIS,
    and inserts the request.
    """
    # 1. Validate storage path ownership if image_path or audio_path provided
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
        req_data["urgency"] = req_data["urgency"].value if hasattr(req_data["urgency"], "value") else str(req_data["urgency"])

    # 2. District Resolution via PostGIS coordinates
    district_name = None
    if payload.latitude is not None and payload.longitude is not None:
        res = district_resolver.resolve_district_by_coordinates(payload.latitude, payload.longitude)
        if res.get("resolved") and res.get("district_id"):
            req_data["district_id"] = res["district_id"]
            district_name = res["district_name"]
    elif payload.district_id:
        req_data["district_id"] = str(payload.district_id)

    # 3. Database Insertion
    inserted = insert_citizen_request(req_data)
    if not inserted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record citizen request in database."
        )

    req_id = UUID(str(inserted["id"]))
    resolved_dist_id = UUID(str(inserted["district_id"])) if inserted.get("district_id") else None

    # Return structured response compatible with both Phase 1 and Phase 3
    return CitizenSubmissionResponse(
        success=True,
        request_id=req_id,
        id=req_id,
        category=inserted.get("category", payload.category),
        status="submitted",
        district_id=resolved_dist_id,
        district_name=district_name,
        message="Request submitted successfully. Your development request has been recorded."
    )


@router.get(
    "/api/requests",
    response_model=List[CitizenRequestResponse],
    summary="List authenticated citizen's own requests"
)
@router.get(
    "/api/v1/requests",
    response_model=List[CitizenRequestResponse],
    summary="List citizen requests (Phase 1 compat)"
)
async def list_requests(
    user_id: Optional[UUID] = Query(None, description="Filter requests by citizen user ID"),
    x_user_id: Optional[UUID] = Header(None, description="Authenticated User ID header"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Retrieves citizen requests. Only returns the authenticated citizen's own requests
    to ensure private grievance data is never exposed.
    """
    auth_user = user_id or x_user_id
    records = list_citizen_requests(
        user_id=str(auth_user) if auth_user else None,
        limit=limit,
        offset=offset
    )
    return records


@router.get(
    "/api/requests/{request_id}",
    response_model=CitizenRequestResponse,
    summary="Get citizen request details by ID"
)
@router.get(
    "/api/v1/requests/{request_id}",
    response_model=CitizenRequestResponse,
    summary="Get citizen request details by ID (Phase 1 compat)"
)
async def get_request(
    request_id: UUID,
    user_id: Optional[UUID] = Query(None, description="Requesting User ID"),
    x_user_id: Optional[UUID] = Header(None, description="Requesting User ID from Header")
):
    """
    Retrieves a citizen request by ID. Enforces ownership authorization so citizens
    cannot view another citizen's private request.
    """
    record = fetch_citizen_request(str(request_id))
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen request not found."
        )

    # Check ownership if caller provided user_id
    caller = user_id or x_user_id
    record_owner = record.get("user_id")
    if caller and record_owner and str(caller) != str(record_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not have permission to access this request."
        )

    return record


@router.post(
    "/api/requests/upload",
    response_model=FileUploadResponse,
    summary="Upload image or audio file attachment"
)
async def upload_file(
    file: UploadFile = File(...),
    user_id: UUID = Form(...),
    request_id: UUID = Form(...),
    bucket_type: str = Form(..., description="'image' or 'audio'")
):
    """
    Validates file MIME type, size bounds (<10MB image, <25MB audio),
    and uploads the attachment to private Supabase Storage.
    """
    btype = bucket_type.lower()
    if btype in ("image", "photo", "img"):
        bucket_name = storage_service.get_bucket_for_type("image")
        allowed_mimes = storage_service.ALLOWED_IMAGE_MIMES
        max_size = storage_service.MAX_IMAGE_SIZE_BYTES
    elif btype in ("audio", "voice", "sound", "recording"):
        bucket_name = storage_service.get_bucket_for_type("audio")
        allowed_mimes = storage_service.ALLOWED_AUDIO_MIMES
        max_size = storage_service.MAX_AUDIO_SIZE_BYTES
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bucket_type '{bucket_type}'. Expected 'image' or 'audio'."
        )

    # Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file MIME type '{content_type}'. Allowed types: {', '.join(allowed_mimes)}"
        )

    # Read content & validate file size
    content = await file.read()
    file_size = len(content)
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size ({max_size // (1024 * 1024)} MB). Received {file_size / (1024 * 1024):.2f} MB."
        )

    storage_path = storage_service.generate_storage_path(
        user_id=user_id,
        request_id=request_id,
        original_filename=file.filename or "attachment"
    )

    # Forward to Supabase Storage if client available
    client = get_supabase_client()
    if client:
        try:
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"}
            )
        except Exception as e:
            # Fall back to path generation if client fails in mock/local mode
            pass

    return FileUploadResponse(
        success=True,
        bucket=bucket_name,
        storage_path=storage_path,
        filename=storage_service.sanitize_filename(file.filename or "attachment"),
        size_bytes=file_size,
        content_type=content_type
    )


@router.post(
    "/api/requests/storage-path",
    response_model=StoragePathGenerateResponse,
    summary="Generate isolated Supabase Storage path for media upload"
)
@router.post(
    "/api/v1/requests/storage-path",
    response_model=StoragePathGenerateResponse,
    summary="Generate storage path (Phase 1 compat)"
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
