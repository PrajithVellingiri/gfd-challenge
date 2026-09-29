"""
Pydantic schemas and sanitization helpers for Multimodal AI Analysis.
Validates raw Gemini JSON output, cleans markdown code fences, and normalizes
categories and urgency levels according to contest specifications.
"""

from typing import List, Optional, Any, Dict
import json
import re
from pydantic import BaseModel, Field, field_validator

ALLOWED_CATEGORIES = [
    "Healthcare",
    "Education",
    "Roads",
    "Water",
    "Transportation",
    "Electricity",
    "Digital Infrastructure",
    "Other",
]

ALLOWED_URGENCIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

CATEGORY_ALIASES = {
    "health": "Healthcare",
    "hospital": "Healthcare",
    "medical": "Healthcare",
    "phc": "Healthcare",
    "school": "Education",
    "college": "Education",
    "educational": "Education",
    "road": "Roads",
    "pothole": "Roads",
    "bridge": "Roads",
    "highway": "Roads",
    "drinking water": "Water",
    "sewage": "Water",
    "drainage": "Water",
    "pipeline": "Water",
    "transport": "Transportation",
    "bus": "Transportation",
    "rail": "Transportation",
    "transit": "Transportation",
    "power": "Electricity",
    "electrical": "Electricity",
    "power cut": "Electricity",
    "transformer": "Electricity",
    "internet": "Digital Infrastructure",
    "broadband": "Digital Infrastructure",
    "telecom": "Digital Infrastructure",
    "network": "Digital Infrastructure",
    "cyber": "Digital Infrastructure",
}


def clean_gemini_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from a Gemini response string that may contain
    markdown code fences (e.g. ```json ... ```) or conversational preamble.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response from AI model")

    cleaned = raw_text.strip()
    # Strip markdown json fences
    fence_pattern = r"^```(?:json)?\s*\n?(.*?)\n?```$"
    match = re.search(fence_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Check if there is a JSON block anywhere in the text
        json_search = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_search:
            cleaned = json_search.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse model response as JSON: {exc}. Raw response: {raw_text[:200]}") from exc


def normalize_category(cat: Optional[str]) -> str:
    """Normalize a category string to one of the 8 canonical categories."""
    if not cat:
        return "Other"
    clean_cat = cat.strip()
    for canonical in ALLOWED_CATEGORIES:
        if clean_cat.lower() == canonical.lower():
            return canonical

    lower_cat = clean_cat.lower()
    for alias, canonical in CATEGORY_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', lower_cat):
            return canonical

    return "Other"


def normalize_urgency(urg: Optional[str]) -> str:
    """Normalize urgency to Low, Medium, High, or Critical."""
    if not urg:
        return "Medium"
    clean_urg = urg.strip().capitalize()
    if clean_urg in ALLOWED_URGENCIES:
        return clean_urg
    return "Medium"


class TextAnalysisResult(BaseModel):
    detected_language: str = Field(..., description="Detected source language")
    translated_text: str = Field(..., description="English translation of request")
    category: str = Field(..., description="Canonical category")
    sub_category: Optional[str] = Field(None, description="Specific sub-category")
    urgency: str = Field("Medium", description="Urgency level")
    summary: str = Field(..., max_length=300, description="Concise summary (<=200 chars preferred)")
    keywords: List[str] = Field(default_factory=list, description="3-10 infrastructure keywords")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return normalize_category(v)

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        return normalize_urgency(v)

    @field_validator("summary")
    @classmethod
    def trim_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 200:
            return v[:197] + "..."
        return v

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, v: List[str]) -> List[str]:
        cleaned = [str(k).strip() for k in v if str(k).strip()]
        # Keep between 3 and 10, or as many as available
        return cleaned[:10]


class ImageAnalysisResult(BaseModel):
    image_relevant: bool = Field(True, description="Whether the image is relevant to public infrastructure")
    infrastructure_type: str = Field("Unknown", description="Observed infrastructure type")
    observations: List[str] = Field(default_factory=list, description="Objective visual observations")
    severity: str = Field("Low", description="Visible physical severity (Low, Medium, High, Critical)")
    summary: str = Field(..., description="Objective summary of visual findings")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        return normalize_urgency(v)

    @field_validator("summary")
    @classmethod
    def trim_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 200:
            return v[:197] + "..."
        return v


class AudioAnalysisResult(BaseModel):
    transcript: str = Field(..., description="Faithful audio transcript")
    detected_language: str = Field(..., description="Detected spoken language")
    translated_text: str = Field(..., description="English translation")
    category: str = Field("Other", description="Canonical category")
    sub_category: Optional[str] = Field(None, description="Specific sub-category")
    urgency: str = Field("Medium", description="Urgency level")
    summary: str = Field(..., description="Concise summary")
    keywords: List[str] = Field(default_factory=list, description="Keywords")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return normalize_category(v)

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        return normalize_urgency(v)

    @field_validator("summary")
    @classmethod
    def trim_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 200:
            return v[:197] + "..."
        return v


class AIRequestAnalysisResponse(BaseModel):
    id: Optional[str] = None
    request_id: str
    prompt_version: str = "v1.0"
    detected_language: Optional[str] = None
    translated_text: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    urgency: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    transcript: Optional[str] = None
    image_analysis: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    processing_status: str = "completed"
    error_message: Optional[str] = None
