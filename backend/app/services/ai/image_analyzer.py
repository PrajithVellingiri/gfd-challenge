"""
Image Analyzer Service for Multimodal Civic Infrastructure Assessment.
"""

from typing import Optional, Dict, Any
import logging
from app.services.ai.gemini_client import GeminiClient, default_gemini_client, GeminiAPIError
from app.services.ai.prompt_templates import IMAGE_ANALYSIS_PROMPT
from app.services.ai.validators import (
    clean_gemini_json_response,
    ImageAnalysisResult
)

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg": True,
    "image/jpg": True,
    "image/png": True,
    "image/webp": True
}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class ImageAnalyzer:
    """Analyzes citizen-submitted infrastructure photos using Gemini Vision."""

    def __init__(self, client: Optional[GeminiClient] = None):
        self.client = client or default_gemini_client

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> ImageAnalysisResult:
        """
        Analyze image bytes using Gemini Vision and return structured results.
        """
        if not image_bytes:
            raise ValueError("No image bytes provided for analysis.")

        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image size exceeds limit of {MAX_IMAGE_SIZE_BYTES / (1024*1024):.0f}MB.")

        canonical_mime = mime_type.lower().strip()
        if canonical_mime == "image/jpg":
            canonical_mime = "image/jpeg"

        if canonical_mime not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError(f"Unsupported image MIME type: {mime_type}. Allowed: JPEG, PNG, WebP.")

        try:
            raw_response = self.client.generate_vision(
                image_bytes=image_bytes,
                mime_type=canonical_mime,
                prompt=IMAGE_ANALYSIS_PROMPT,
                temperature=0.2
            )
            parsed_data = clean_gemini_json_response(raw_response)
            return ImageAnalysisResult(**parsed_data)
        except Exception as exc:
            logger.warning("Image analysis failed: %s", exc)
            raise


# Default global instance
default_image_analyzer = ImageAnalyzer()
