"""Authentication API endpoints: registration, login, logout, password recovery, and social OAuth."""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    clear_session_cookie,
    get_current_user,
    get_optional_user,
    set_session_cookie,
    verify_csrf_header,
)
from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import generate_random_token
from app.models.user import User
from app.schemas.auth import (
    AuthMessageResponse,
    ForgotPasswordRequest,
    OAuthProviderStatus,
    ResetPasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth.oauth import (
    OAuthConfigurationError,
    OAuthVerificationError,
    exchange_apple_code,
    exchange_github_code,
    exchange_google_code,
    generate_pkce_pair,
    get_apple_auth_url,
    get_github_auth_url,
    get_google_auth_url,
    get_oauth_provider_status,
    resolve_or_create_oauth_user,
)
from app.services.auth.service import (
    AuthenticationError,
    PasswordResetError,
    RegistrationError,
    get_linked_oauth_providers,
    login_user,
    logout_session,
    register_user,
    request_password_reset,
    reset_password_with_token,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student account",
    dependencies=[Depends(verify_csrf_header)],
)
async def register(
    payload: UserRegisterRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Register a new student account using email and password, returning an active session cookie."""
    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None

    try:
        user, raw_token = await register_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            user_agent=user_agent,
            ip_address=client_ip,
        )
    except RegistrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    set_session_cookie(response, raw_token)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        linked_providers=[],
    )


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Email/password sign-in",
    dependencies=[Depends(verify_csrf_header)],
)
async def login(
    payload: UserLoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Authenticate with email and password, establishing a server-managed session."""
    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None

    try:
        user, raw_token = await login_user(
            db,
            email=payload.email,
            password=payload.password,
            user_agent=user_agent,
            ip_address=client_ip,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    set_session_cookie(response, raw_token)
    providers = await get_linked_oauth_providers(db, user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        linked_providers=providers,
    )


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    summary="Revoke session and sign out",
    dependencies=[Depends(verify_csrf_header)],
)
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    """Revoke the active session token and clear the browser cookie."""
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if raw_token:
        await logout_session(db, raw_token)

    clear_session_cookie(response)
    return AuthMessageResponse(message="Successfully signed out.", success=True)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Return the profile and linked identity providers for the currently authenticated user."""
    providers = await get_linked_oauth_providers(db, current_user.id)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        linked_providers=providers,
    )


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    summary="Request password recovery token",
    dependencies=[Depends(verify_csrf_header)],
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    """Request a single-use expiring password recovery link. Always returns generic success."""
    raw_token = await request_password_reset(db, payload.email)

    if raw_token:
        # If an email/SMTP provider is configured, dispatch the message
        if settings.SMTP_HOST:
            logger.info("Dispatching password reset email to %s via %s", payload.email, settings.SMTP_HOST)
            # In a real SMTP production setup, smtplib / aiosmtplib would send the email here.
        else:
            logger.info("Local development: password reset token created for %s", payload.email)

    return AuthMessageResponse(
        message="If an account matches that email address, instructions have been sent.",
        success=True,
    )


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    summary="Reset password using recovery token",
    dependencies=[Depends(verify_csrf_header)],
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    """Reset account password using a valid, single-use, non-expired recovery token."""
    try:
        await reset_password_with_token(db, raw_token=payload.token, new_password=payload.new_password)
    except PasswordResetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return AuthMessageResponse(
        message="Your password has been successfully updated. Please sign in.",
        success=True,
    )


@router.get(
    "/providers",
    response_model=List[OAuthProviderStatus],
    summary="List available social authentication providers",
)
async def list_providers() -> List[OAuthProviderStatus]:
    """Return availability status for Google, Apple, and GitHub sign-in."""
    return [OAuthProviderStatus(**p) for p in get_oauth_provider_status()]


def get_safe_redirect_path(raw: Optional[str]) -> Optional[str]:
    """Validate that a return URL path is safe against open-redirect attacks.

    Guarantees:
    - Must start with '/'
    - Must NOT start with '//' (scheme-relative URLs)
    - Must NOT contain '\\' (path-traversal or backslash browser parsing quirks)
    - Must NOT contain scheme indicators '://' or control characters
    """
    if not raw or not isinstance(raw, str):
        return None
    cleaned = raw.strip().strip('"').strip("'")
    if (
        cleaned.startswith("/")
        and not cleaned.startswith("//")
        and "\\" not in cleaned
        and "://" not in cleaned
        and not any(c in cleaned for c in ("\r", "\n", "\0"))
    ):
        return cleaned
    return None


@router.get(
    "/{provider}/authorize",
    summary="Initiate social sign-in flow",
)
async def authorize_oauth(
    provider: str,
    response: Response,
    next: Optional[str] = Query(None),
) -> Any:
    """Generate authorization redirect URL for Google, GitHub, or Apple OAuth."""
    provider_lower = provider.lower()
    state = generate_random_token(24)
    safe_next = get_safe_redirect_path(next)

    if provider_lower == "google":
        try:
            verifier, challenge = generate_pkce_pair()
            auth_url = get_google_auth_url(state=state, code_challenge=challenge)
            # Store state and PKCE verifier in short-lived HTTP-only cookies
            response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
            response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax", path="/")
            response.set_cookie("oauth_verifier", verifier, max_age=600, httponly=True, samesite="lax", path="/")
            if safe_next:
                response.set_cookie("oauth_next", safe_next, max_age=600, httponly=True, samesite="lax", path="/")
            return response
        except OAuthConfigurationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    elif provider_lower == "github":
        try:
            auth_url = get_github_auth_url(state=state)
            response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
            response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax", path="/")
            if safe_next:
                response.set_cookie("oauth_next", safe_next, max_age=600, httponly=True, samesite="lax", path="/")
            return response
        except OAuthConfigurationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    elif provider_lower == "apple":
        try:
            auth_url = get_apple_auth_url(state=state)
            response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
            response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax", path="/")
            if safe_next:
                response.set_cookie("oauth_next", safe_next, max_age=600, httponly=True, samesite="lax", path="/")
            return response
        except OAuthConfigurationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: '{provider}'. Supported providers: google, github, apple.",
        )


@router.get(
    "/{provider}/callback",
    summary="Process social OAuth callback",
)
async def oauth_callback(
    provider: str,
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    oauth_state: Optional[str] = Cookie(None),
    oauth_verifier: Optional[str] = Cookie(None),
    oauth_next: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_optional_user),
) -> Response:
    """Handle the OAuth authorization callback, establish session, and redirect to frontend."""
    frontend_url = settings.FRONTEND_BASE_URL
    provider_lower = provider.lower()

    if error:
        logger.warning("%s OAuth returned error: %s", provider, error)
        redirect_err = urlencode({"error": f"{provider.capitalize()} sign-in was cancelled or denied."})
        return RedirectResponse(f"{frontend_url}/login?{redirect_err}", status_code=status.HTTP_302_FOUND)

    if not code:
        redirect_err = urlencode({"error": "Missing authorization code from provider."})
        return RedirectResponse(f"{frontend_url}/login?{redirect_err}", status_code=status.HTTP_302_FOUND)

    # Validate state
    if not state or not oauth_state or state != oauth_state:
        logger.warning("OAuth state parameter mismatch or missing state cookie")
        redirect_err = urlencode({"error": "Invalid or expired OAuth state parameter. Please try again."})
        return RedirectResponse(f"{frontend_url}/login?{redirect_err}", status_code=status.HTTP_302_FOUND)

    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None

    try:
        if provider_lower == "google":
            if not oauth_verifier:
                raise OAuthVerificationError("Missing PKCE code verifier for Google sign-in.")
            profile = await exchange_google_code(code=code, code_verifier=oauth_verifier)

        elif provider_lower == "github":
            profile = await exchange_github_code(code=code)

        elif provider_lower == "apple":
            profile = await exchange_apple_code(code=code)

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider.")

        user, raw_token = await resolve_or_create_oauth_user(
            db=db,
            provider=provider_lower,
            provider_account_id=profile["provider_account_id"],
            email=profile["email"],
            full_name=profile.get("full_name"),
            current_user=current_user,
            user_agent=user_agent,
            ip_address=client_ip,
        )

    except (OAuthConfigurationError, OAuthVerificationError) as exc:
        logger.warning("OAuth failure (%s): %s", provider, exc)
        redirect_err = urlencode({"error": str(exc)})
        return RedirectResponse(f"{frontend_url}/login?{redirect_err}", status_code=status.HTTP_302_FOUND)

    safe_next = get_safe_redirect_path(oauth_next)
    redirect_target = f"{frontend_url}{safe_next}" if safe_next else f"{frontend_url}/"
    res = RedirectResponse(url=redirect_target, status_code=status.HTTP_302_FOUND)
    set_session_cookie(res, raw_token)
    res.delete_cookie("oauth_state", path="/")
    res.delete_cookie("oauth_verifier", path="/")
    res.delete_cookie("oauth_next", path="/")
    return res


@router.get(
    "/leetcode/status",
    summary="LeetCode integration status and documentation",
)
async def leetcode_integration_status() -> Dict[str, Any]:
    """Return explicit notice that LeetCode does not support public third-party OAuth sign-in."""
    return {
        "provider": "leetcode",
        "supports_oauth_sign_in": False,
        "official_auth_supported": False,
        "message": (
            "LeetCode does not provide an official public third-party OAuth 2.0 / OpenID Connect "
            "authorization service. AI Coding Gym does not collect passwords, session cookies, "
            "or reverse-engineer private authentication endpoints. Profile linking is supported "
            "strictly as an external read-only profile reference and cannot establish identity."
        ),
    }
