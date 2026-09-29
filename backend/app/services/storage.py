import os
import re
from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from app.config import settings
from app.db import get_supabase_client


class StorageService:
    """
    Manages Supabase Storage operations and path generation.
    Enforces user-isolated directory hierarchies: {user_id}/{request_id}/{filename}
    Ensures binary files are never stored in PostgreSQL.
    """

    ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    ALLOWED_AUDIO_MIMES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/webm", "audio/x-m4a"]

    MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitizes a filename to prevent directory traversal and invalid characters.
        """
        # Strip path traversal attempts and get base name
        base = os.path.basename(filename)
        # Keep only alphanumeric, hyphen, underscore, and dot
        cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base)
        return cleaned or "upload"

    def get_bucket_for_type(self, file_type: str) -> str:
        """
        Returns bucket name corresponding to file type ('image' or 'audio').
        """
        t = file_type.lower()
        if t in ("image", "photo", "img"):
            return settings.STORAGE_IMAGE_BUCKET
        elif t in ("audio", "voice", "sound", "recording"):
            return settings.STORAGE_AUDIO_BUCKET
        raise ValueError(f"Unsupported file type '{file_type}'. Supported types: 'image', 'audio'.")

    def generate_storage_path(
        self,
        user_id: UUID,
        request_id: UUID,
        original_filename: str,
        prefix: Optional[str] = None
    ) -> str:
        """
        Generates a secure, deterministic Supabase Storage object path:
        Format: {user_id}/{request_id}/{prefix_or_clean_filename}
        """
        clean_name = self.sanitize_filename(original_filename)
        if prefix:
            clean_name = f"{prefix}_{clean_name}"
        return f"{user_id}/{request_id}/{clean_name}"

    def validate_storage_path_owner(self, storage_path: str, expected_user_id: UUID) -> bool:
        """
        Validates that a given storage path begins with the user's ID to prevent
        cross-user storage reference hijacking.
        """
        parts = storage_path.strip("/").split("/")
        if not parts or parts[0] != str(expected_user_id):
            return False
        return True

    def create_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generates a time-limited signed URL for private bucket objects.
        Requires active Supabase client.
        """
        client = get_supabase_client()
        if not client:
            return None
        try:
            res = client.storage.from_(bucket).create_signed_url(path, expires_in)
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            elif hasattr(res, "signed_url"):
                return res.signed_url
            return None
        except Exception:
            return None


storage_service = StorageService()
