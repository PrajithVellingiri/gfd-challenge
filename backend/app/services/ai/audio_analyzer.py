"""
Audio Analyzer Service for Citizen Voice Note Transcription and Reasoning.
"""

from typing import Optional
import logging
from backend.app.services.ai.gemini_client import GeminiClient, default_gemini_client
from backend.app.services.ai.prompt_templates import AUDIO_ANALYSIS_PROMPT
from backend.app.services.ai.validators import (
    clean_gemini_json_response,
    AudioAnalysisResult
)

logger = logging.getLogger(__name__)

ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm": True,
    "audio/wav": True,
    "audio/x-wav": True,
    "audio/mp3": True,
    "audio/mpeg": True,
    "audio/mp4": True,
    "audio/aac": True,
    "audio/ogg": True,
    "audio/flac": True
}
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class AudioAnalyzer:
    """Transcribes and analyzes citizen voice notes using Gemini Multimodal Audio."""

    def __init__(self, client: Optional[GeminiClient] = None):
        self.client = client or default_gemini_client

    def analyze_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm"
    ) -> AudioAnalysisResult:
        """
        Analyze audio bytes using Gemini and return structured transcript + civic analysis.
        """
        if not audio_bytes:
            raise ValueError("No audio bytes provided for analysis.")

        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise ValueError(f"Audio size exceeds limit of {MAX_AUDIO_SIZE_BYTES / (1024*1024):.0f}MB.")

        canonical_mime = mime_type.lower().strip()
        if canonical_mime == "audio/x-wav":
            canonical_mime = "audio/wav"
        elif canonical_mime == "audio/mp3":
            canonical_mime = "audio/mpeg"

        if canonical_mime not in ALLOWED_AUDIO_MIME_TYPES:
            raise ValueError(f"Unsupported audio MIME type: {mime_type}. Allowed: WebM, WAV, MP3, MP4, AAC, OGG.")

        try:
            raw_response = self.client.generate_audio(
                audio_bytes=audio_bytes,
                mime_type=canonical_mime,
                prompt=AUDIO_ANALYSIS_PROMPT,
                temperature=0.2
            )
            parsed_data = clean_gemini_json_response(raw_response)
            return AudioAnalysisResult(**parsed_data)
        except Exception as exc:
            logger.warning("Audio analysis failed: %s", exc)
            raise


# Default global instance
default_audio_analyzer = AudioAnalyzer()
