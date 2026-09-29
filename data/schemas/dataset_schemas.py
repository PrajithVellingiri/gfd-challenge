from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class DistrictModel(BaseModel):
    id: UUID
    name: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    country: str = Field(default="India")
    population_ref: Optional[int] = Field(default=None, ge=0)
    boundary: Dict[str, Any]
    centroid: Dict[str, float]
    bbox: List[float]


class DemographicsModel(BaseModel):
    district_id: UUID
    district_name: str
    state: str
    country: str = "India"
    population: int = Field(..., gt=0)
    rural_population: int = Field(..., ge=0)
    urban_population: int = Field(..., ge=0)
    demographic_indicators: Dict[str, Any]
    year: int = Field(..., ge=1900, le=2100)
    source: str
    data_type: str = Field(default="official", pattern="^(official|public|synthetic)$")

    @field_validator("rural_population", mode="after")
    @classmethod
    def validate_rural_urban_sum(cls, v, info):
        # Additional custom validation if needed
        return v


class InfrastructureModel(BaseModel):
    district_id: UUID
    district_name: str
    state: str
    country: str = "India"
    category: str = Field(..., min_length=2)
    name: str = Field(..., min_length=2)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    capacity_value: Dict[str, Any] = Field(default_factory=dict)
    source: str
    source_reference: Optional[str] = None
    year: Optional[int] = None
    data_type: str = Field(default="official", pattern="^(official|public|synthetic)$")


class HealthIndicatorModel(BaseModel):
    district_id: UUID
    district_name: str
    state: str
    country: str = "India"
    indicator_name: str = Field(..., min_length=2)
    indicator_value: float = Field(..., ge=0.0, le=100.0)
    unit: str = "%"
    year: int = Field(..., ge=1990, le=2030)
    source: str
    source_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data_type: str = Field(default="official", pattern="^(official|public|synthetic)$")


class InvestmentModel(BaseModel):
    district_id: UUID
    district_name: str
    state: str
    country: str = "India"
    category: str = Field(..., min_length=2)
    amount: float = Field(..., ge=0.0)
    currency: str = "INR"
    financial_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    source: str
    source_reference: Optional[str] = None
    data_type: str = Field(default="synthetic", pattern="^(official|public|synthetic)$")


class CitizenDemandModel(BaseModel):
    id: UUID
    district_id: UUID
    district_name: str
    state: str
    country: str = "India"
    category: str = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
    language: str
    urgency: str = Field(..., pattern="^(low|medium|high|critical)$")
    status: str = "submitted"
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: Optional[str] = None
    source_type: str = Field(default="web", pattern="^(web|mobile_app|ivr|sms)$")
    is_synthetic: bool = True
    data_type: str = Field(default="synthetic", pattern="^(synthetic)$")
    created_at: str
    updated_at: str
