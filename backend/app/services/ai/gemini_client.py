"""
Google Gemini Multimodal API Client Wrapper.
Provides clean interfaces for text, vision, and audio processing using the Gemini API.
"""

from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Raised when communication with Gemini API fails."""
    pass


class GeminiClient:
    """
    Client for interacting with Google Gemini models.
    Supports text generation, vision inspection, and audio transcription/analysis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._genai_configured = False

    def _ensure_configured(self):
        """Configure google.generativeai with API key."""
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY is not configured in environment.")

        if not self._genai_configured:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai_configured = True
            except Exception as exc:
                raise GeminiAPIError(f"Failed to configure Google Generative AI: {exc}") from exc

    def _get_model(self, system_instruction: Optional[str] = None):
        """Get GenerativeModel instance."""
        self._ensure_configured()
        import google.generativeai as genai
        kwargs: Dict[str, Any] = {"model_name": self.model_name}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
        return genai.GenerativeModel(**kwargs)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Send text prompt to Gemini model and return text response.
        """
        try:
            model = self._get_model(system_instruction=system_instruction)
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
            }
            response = model.generate_content(
                contents=[prompt],
                generation_config=generation_config
            )
            if not response or not hasattr(response, "text") or not response.text:
                raise GeminiAPIError("Gemini returned empty text response.")
            return response.text
        except GeminiAPIError:
            raise
        except Exception as exc:
            logger.error("Gemini text generation failed: %s", exc)
            raise GeminiAPIError(f"Gemini text generation error: {exc}") from exc

    def generate_vision(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Send image and prompt to Gemini model and return text response.
        """
        try:
            model = self._get_model(system_instruction=system_instruction)
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
            }
            response = model.generate_content(
                contents=[prompt, image_part],
                generation_config=generation_config
            )
            if not response or not hasattr(response, "text") or not response.text:
                raise GeminiAPIError("Gemini returned empty response for image analysis.")
            return response.text
        except GeminiAPIError:
            raise
        except Exception as exc:
            logger.error("Gemini vision analysis failed: %s", exc)
            raise GeminiAPIError(f"Gemini vision analysis error: {exc}") from exc

    def generate_audio(
        self,
        audio_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Send audio and prompt to Gemini model and return text response.
        """
        try:
            model = self._get_model(system_instruction=system_instruction)
            audio_part = {
                "mime_type": mime_type,
                "data": audio_bytes
            }
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
            }
            response = model.generate_content(
                contents=[prompt, audio_part],
                generation_config=generation_config
            )
            if not response or not hasattr(response, "text") or not response.text:
                raise GeminiAPIError("Gemini returned empty response for audio analysis.")
            return response.text
        except GeminiAPIError:
            raise
        except Exception as exc:
            logger.error("Gemini audio analysis failed: %s", exc)
            raise GeminiAPIError(f"Gemini audio analysis error: {exc}") from exc


# Default global instance
default_gemini_client = GeminiClient()
