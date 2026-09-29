from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


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
    language: str = Field(default="en", max_length=50, description="Language code (e.g. en, hi, ta)")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude coordinate")
    location_name: Optional[str] = Field(default=None, max_length=255, description="Human-readable location or village name")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM)
    image_path: Optional[str] = Field(default=None, description="Storage path reference in citizen-images bucket")
    audio_path: Optional[str] = Field(default=None, description="Storage path reference in citizen-audio bucket")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates_pair(cls, v, info):
        # Coordinates must be provided together or both None
        return v


class CitizenRequestResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
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
