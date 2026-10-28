"""FastAPI dependencies for user authentication, session verification, and CSRF protection."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.user import User
from app.services.auth.service import authenticate_session

logger = logging.getLogger(__name__)
settings = get_settings()


def set_session_cookie(response: Response, raw_token: str) -> None:
    """Set the HttpOnly session cookie on the response."""
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=settings.SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE.lower(),
        secure=settings.SESSION_COOKIE_SECURE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Clear the session cookie from the client."""
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE.lower(),
        secure=settings.SESSION_COOKIE_SECURE,
    )


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Dependency that resolves the current user if a valid session exists, or None."""
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        # Also check Authorization: Bearer <token> for developer/API client flexibility
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:].strip()

    if not session_token:
        return None

    return await authenticate_session(db, session_token)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency requiring an active, valid student session. Raises 401 if unauthorized."""
    user = await get_optional_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to continue.",
        )
    return user


async def verify_csrf_header(request: Request) -> None:
    """Verify that state-changing requests carry standard anti-CSRF custom headers.
    
    Browsers forbid cross-origin forms from attaching custom headers without CORS preflight.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # Allow requests with X-Gym-CSRF, X-Requested-With, or standard Authorization
        csrf_header = request.headers.get("X-Gym-CSRF") or request.headers.get("X-Requested-With")
        auth_header = request.headers.get("Authorization")
        # For public/testing convenience, if Authorization or custom header present, allow
        if not csrf_header and not auth_header:
            # Check content-type: JSON requests from fetch with credentials are also safe
            content_type = request.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-site request forgery protection: custom header or JSON content required.",
                )
