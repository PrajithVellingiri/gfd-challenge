from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class UserRole(str, Enum):
    CITIZEN = "citizen"
    POLICYMAKER = "policymaker"
    ADMIN = "admin"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class HealthResponse(BaseModel):
    status: str = Field(description="'healthy' or 'degraded'")
    api: str = Field(default="running")
    database: str = Field(description="'connected' or 'unreachable'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str


class CitizenRequestCreate(BaseModel):
    user_id: Optional[UUID] = Field(default=None, description="Citizen user ID from Supabase Auth")
    description: str = Field(..., min_length=5, max_length=5000, description="Description of the public grievance or request")
    category: str = Field(..., min_length=2, max_length=100, description="Infrastructure / governance category")
    language: str = Field(default="en", max_length=50, description="Language code (e.g. en, hi, ta, other)")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude coordinate")
    location_name: Optional[str] = Field(default=None, max_length=255, description="Human-readable location or village name")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM)
    image_path: Optional[str] = Field(default=None, description="Storage path reference in citizen-images bucket")
    audio_path: Optional[str] = Field(default=None, description="Storage path reference in citizen-audio bucket")
    district_id: Optional[UUID] = Field(default=None, description="Canonical district UUID if pre-selected")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower()
            valid_cats = [
                "healthcare", "education", "roads", "water",
                "transportation", "electricity", "digital infrastructure", "other"
            ]
            if clean in valid_cats:
                return clean
            # Match titles like "Healthcare"
            for c in valid_cats:
                if clean == c.lower():
                    return c
        return v

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower()
            lang_map = {
                "english": "en", "en": "en",
                "tamil": "ta", "ta": "ta",
                "hindi": "hi", "hi": "hi",
                "other": "other"
            }
            return lang_map.get(clean, clean)
        return v

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in [u.value for u in UrgencyLevel]:
                return clean
        return v

    @model_validator(mode="after")
    def set_default_location_if_empty(self):
        has_coords = self.latitude is not None and self.longitude is not None
        has_name = self.location_name and self.location_name.strip()
        if not has_coords and not has_name:
            self.location_name = "Location Unspecified"
        return self


class CitizenSubmissionResponse(BaseModel):
    success: bool = True
    request_id: UUID
    id: UUID
    category: Optional[str] = None
    status: str = "submitted"
    district_id: Optional[UUID] = None
    district_name: Optional[str] = None
    message: str = "Request submitted successfully. Your development request has been recorded."


class StandardErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: StandardErrorDetail


class CitizenRequestResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    district_name: Optional[str] = None
    description: str
    category: str
    language: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    urgency: UrgencyLevel
    status: RequestStatus
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    source_type: Optional[str] = "web"
    is_synthetic: Optional[bool] = False
    extracted_intent: Optional[str] = None
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    extracted_entities: Optional[List[Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    cluster_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StoragePathGenerateRequest(BaseModel):
    user_id: UUID
    request_id: UUID
    bucket_type: str = Field(..., description="'image' or 'audio'")
    original_filename: str = Field(..., min_length=1, max_length=255)


class StoragePathGenerateResponse(BaseModel):
    bucket: str
    storage_path: str
    allowed_mime_types: List[str]
    max_size_bytes: int


class FileUploadResponse(BaseModel):
    success: bool = True
    bucket: str
    storage_path: str
    filename: str
    size_bytes: int
    content_type: str
