"""
Authentication & Authorization Dependencies for Protected Endpoints.
Protects administrative, batch intelligence, and refresh operations.
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from app.config import settings


def verify_admin_authorization(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """
    Enforces authorization on sensitive administrative, batch processing, and refresh endpoints.
    
    Access is granted if:
    1. A valid X-Admin-Key matching settings.ADMIN_API_KEY is supplied.
    2. A valid Bearer token matching settings.ADMIN_API_KEY or settings.SUPABASE_SERVICE_ROLE_KEY is supplied.
    3. The caller presents an authenticated admin role (X-User-Role: admin).
    4. In non-production environments when no ADMIN_API_KEY has been configured.
    """
    is_prod = settings.ENVIRONMENT.lower() == "production"

    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ", 1)[1].strip()

    provided_key = x_admin_key or bearer_token

    # In production or if ADMIN_API_KEY is explicitly configured
    if is_prod or settings.ADMIN_API_KEY:
        valid_keys = [k for k in [settings.ADMIN_API_KEY, settings.SUPABASE_SERVICE_ROLE_KEY] if k]
        if provided_key and provided_key in valid_keys:
            return True
        if x_user_role == "admin":
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative credentials or valid admin key required."
        )

    return True
