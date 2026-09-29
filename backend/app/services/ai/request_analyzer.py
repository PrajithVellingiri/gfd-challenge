"""
Master Multimodal Request Analyzer Service.
Coordinates text analysis, voice note transcription, and vision inspection,
normalizing outputs and saving structured results to public.ai_analyses.
"""

from typing import Optional, Dict, Any, Union
from uuid import UUID
import logging

from backend.app.config import settings
from backend.app.services.ai.gemini_client import GeminiClient, default_gemini_client, GeminiAPIError
from backend.app.services.ai.image_analyzer import ImageAnalyzer, default_image_analyzer
from backend.app.services.ai.audio_analyzer import AudioAnalyzer, default_audio_analyzer
from backend.app.services.ai.prompt_templates import PROMPT_VERSION, TEXT_ANALYSIS_SYSTEM_PROMPT
from backend.app.services.ai.validators import (
    clean_gemini_json_response,
    normalize_category,
    normalize_urgency,
    TextAnalysisResult,
    AIRequestAnalysisResponse,
)
from backend.app.db import get_supabase_client

logger = logging.getLogger(__name__)


class RequestAnalyzer:
    """
    Multimodal AI intelligence orchestrator.
    Processes text, audio, and visual grievance data via Google Gemini models.
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        image_analyzer: Optional[ImageAnalyzer] = None,
        audio_analyzer: Optional[AudioAnalyzer] = None
    ):
        self.gemini_client = gemini_client or default_gemini_client
        self.image_analyzer = image_analyzer or ImageAnalyzer(client=self.gemini_client)
        self.audio_analyzer = audio_analyzer or AudioAnalyzer(client=self.gemini_client)

    def analyze_text(self, text: str) -> TextAnalysisResult:
        """
        Analyze citizen description text with Gemini.
        Detects language, translates to English, identifies category, sub-category,
        urgency, summary, and keywords.
        """
        if not text or not text.strip():
            raise ValueError("No text provided for analysis.")

        prompt = f"Citizen Submission:\n\"\"\"\n{text.strip()}\n\"\"\"\n\nReturn strictly valid JSON according to instructions."
        raw_response = self.gemini_client.generate_text(
            prompt=prompt,
            system_instruction=TEXT_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2
        )
        parsed_json = clean_gemini_json_response(raw_response)
        return TextAnalysisResult(**parsed_json)

    def download_storage_file(self, bucket: str, path: str) -> Optional[bytes]:
        """
        Attempts to download media file bytes from Supabase Storage.
        """
        client = get_supabase_client()
        if not client:
            return None
        try:
            res = client.storage.from_(bucket).download(path)
            if isinstance(res, bytes):
                return res
            elif hasattr(res, "content"):
                return res.content
            return None
        except Exception as exc:
            logger.warning("Failed to download file from storage bucket %s, path %s: %s", bucket, path, exc)
            return None

    def analyze_citizen_request(
        self,
        request_id: Union[str, UUID],
        description: Optional[str] = None,
        title: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: str = "image/jpeg",
        image_path: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime: str = "audio/webm",
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multimodal analysis on a citizen request.
        Safely captures failures and transitions processing_status to 'failed'
        without corrupting or deleting the underlying request.
        """
        req_id_str = str(request_id)
        result: Dict[str, Any] = {
            "request_id": req_id_str,
            "prompt_version": PROMPT_VERSION,
            "detected_language": None,
            "translated_text": None,
            "category": "Other",
            "sub_category": None,
            "urgency": "Medium",
            "summary": None,
            "keywords": [],
            "transcript": None,
            "image_analysis": {},
            "confidence": None,
            "processing_status": "processing",
            "error_message": None
        }

        # Check for Gemini API key
        if not self.gemini_client.api_key:
            result["processing_status"] = "failed"
            result["error_message"] = "Google Gemini API key is not configured in backend environment."
            logger.warning("Gemini API key missing for request %s", req_id_str)
            return result

        try:
            # 1. Download storage files if bytes were not directly supplied
            if not image_bytes and image_path:
                image_bytes = self.download_storage_file(settings.STORAGE_IMAGE_BUCKET, image_path)

            if not audio_bytes and audio_path:
                audio_bytes = self.download_storage_file(settings.STORAGE_AUDIO_BUCKET, audio_path)

            has_text = bool(description and description.strip())
            has_audio = bool(audio_bytes)
            has_image = bool(image_bytes)

            if not has_text and not has_audio and not has_image:
                result["processing_status"] = "failed"
                result["error_message"] = "No text description, audio recording, or image attachment provided."
                return result

            # 2. Audio Processing (Transcription + Classification)
            audio_result = None
            if has_audio:
                try:
                    audio_result = self.audio_analyzer.analyze_audio(
                        audio_bytes=audio_bytes,
                        mime_type=audio_mime
                    )
                    result["transcript"] = audio_result.transcript
                    result["detected_language"] = audio_result.detected_language
                    result["translated_text"] = audio_result.translated_text
                    result["category"] = audio_result.category
                    result["sub_category"] = audio_result.sub_category
                    result["urgency"] = audio_result.urgency
                    result["summary"] = audio_result.summary
                    result["keywords"] = audio_result.keywords
                except Exception as exc:
                    logger.error("Audio analysis failed for request %s: %s", req_id_str, exc)
                    if not has_text and not has_image:
                        raise

            # 3. Text Processing (Description)
            if has_text:
                full_text = f"Title: {title.strip()}\n\n{description.strip()}" if title and title.strip() else description.strip()
                text_result = self.analyze_text(full_text)

                result["detected_language"] = text_result.detected_language
                result["translated_text"] = text_result.translated_text
                result["category"] = text_result.category
                result["sub_category"] = text_result.sub_category
                result["urgency"] = text_result.urgency
                result["summary"] = text_result.summary
                result["keywords"] = text_result.keywords

                # If audio was also present, append or reconcile
                if audio_result and audio_result.transcript:
                    result["transcript"] = audio_result.transcript
                    # Blend keywords uniquely
                    combined_kw = list(dict.fromkeys(result["keywords"] + audio_result.keywords))
                    result["keywords"] = combined_kw[:10]

            # 4. Image Processing (Visual Observations)
            if has_image:
                try:
                    img_result = self.image_analyzer.analyze_image(
                        image_bytes=image_bytes,
                        mime_type=image_mime
                    )
                    result["image_analysis"] = img_result.model_dump()
                except Exception as exc:
                    logger.warning("Image analysis failed for request %s: %s", req_id_str, exc)
                    result["image_analysis"] = {
                        "image_relevant": False,
                        "infrastructure_type": "Unknown",
                        "observations": [f"Visual analysis unavailable: {str(exc)}"],
                        "severity": "Low",
                        "summary": "Visual analysis could not be completed."
                    }

            result["processing_status"] = "completed"
            result["error_message"] = None

        except Exception as exc:
            logger.exception("AI Analysis orchestration failed for request %s", req_id_str)
            result["processing_status"] = "failed"
            result["error_message"] = str(exc)

        return result


# Default global instance
default_request_analyzer = RequestAnalyzer()
