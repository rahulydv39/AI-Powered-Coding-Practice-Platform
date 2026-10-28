"""Security hardening and regression test suite for Phase 5.3.

Covers:
1. Session cookie attributes (HttpOnly, SameSite, Path).
2. Expired session token rejection (401).
3. CSRF protection verification on state-changing requests.
4. OAuth account hijacking prevention for existing password accounts.
5. Apple OAuth callback integration and error handling.
6. Password reset token expiry validation.
7. CORS credentials and origin security verification.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, hash_token
from app.main import app
from app.models.user import PasswordResetToken, User, UserOAuthAccount, UserSession

settings = get_settings()


@pytest.fixture
async def clean_async_client() -> AsyncClient:
    """Async test client without default authentication overrides."""
    saved_override = app.dependency_overrides.pop(get_current_user, None)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
    if saved_override:
        app.dependency_overrides[get_current_user] = saved_override


@pytest.mark.asyncio
async def test_session_cookie_security_attributes(clean_async_client: AsyncClient) -> None:
    """Verify session cookie contains HttpOnly, SameSite, and Path attributes."""
    unique_email = f"cookie_sec_{datetime.now().timestamp()}@example.com"
    payload = {"email": unique_email, "password": "Password123!"}
    headers = {"X-Gym-CSRF": "1"}

    resp = await clean_async_client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201

    # Inspect Set-Cookie header
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert settings.SESSION_COOKIE_NAME in set_cookie_header
    assert "httponly" in set_cookie_header.lower()
    assert "samesite=lax" in set_cookie_header.lower()
    assert "path=/" in set_cookie_header.lower()


@pytest.mark.asyncio
async def test_expired_session_rejected(clean_async_client: AsyncClient) -> None:
    """Sessions with expires_at in the past must be rejected with 401."""
    ts = datetime.now().timestamp()
    email = f"expired_sess_{ts}@example.com"
    raw_token = f"raw_expired_token_{ts}"
    token_hash = hash_token(raw_token)

    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password("Password123!"),
            is_active=True,
        )
        db.add(user)
        await db.flush()

        expired_session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            # Expired 1 hour ago
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(expired_session)
        await db.commit()

    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, raw_token)
    resp = await clean_async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "authentication required" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_csrf_protection_rejects_unsafe_form_requests(clean_async_client: AsyncClient) -> None:
    """State-changing requests with form-urlencoded body and no CSRF header must return 403."""
    resp = await clean_async_client.post(
        "/api/v1/auth/login",
        content=b"email=test@example.com&password=secret",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 403
    err_body = resp.json()
    msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "forgery" in msg.lower()


@pytest.mark.asyncio
async def test_oauth_account_hijacking_prevention(clean_async_client: AsyncClient) -> None:
    """An external OAuth callback cannot take over an existing email that has a password."""
    ts = datetime.now().timestamp()
    email = f"preexisting_{int(ts)}@example.com"

    # 1. Create a user with email/password
    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password("SuperSecret123!"),
            is_active=True,
        )
        db.add(user)
        await db.commit()

    # 2. Attempt Google OAuth callback with the same email address
    state = "test_hijack_state"
    clean_async_client.cookies.set("oauth_state", state)
    clean_async_client.cookies.set("oauth_verifier", "test_verifier")

    mock_profile = {
        "provider_account_id": f"google_hijacker_{int(ts)}",
        "email": email,
        "full_name": "Potential Hijacker",
    }

    with patch("app.api.v1.endpoints.auth.exchange_google_code", return_value=mock_profile):
        resp = await clean_async_client.get(
            f"/api/v1/auth/google/callback?code=mock_code&state={state}",
            follow_redirects=False,
        )
        # Must redirect to login with error rather than establishing session
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]
        assert "error=" in resp.headers["location"]
        # Ensure session was not created for hijacker
        assert resp.cookies.get(settings.SESSION_COOKIE_NAME) is None


@pytest.mark.asyncio
async def test_apple_oauth_callback_flow(clean_async_client: AsyncClient) -> None:
    """Mocked Apple OAuth callback creates user and session cookie."""
    ts = datetime.now().timestamp()
    apple_sub = f"apple_sub_{int(ts)}"
    apple_email = f"apple_user_{int(ts)}@example.com"
    state = "apple_state_789"

    mock_profile = {
        "provider_account_id": apple_sub,
        "email": apple_email,
        "full_name": "Apple Student",
    }

    clean_async_client.cookies.set("oauth_state", state)

    with patch("app.api.v1.endpoints.auth.exchange_apple_code", return_value=mock_profile):
        resp = await clean_async_client.get(
            f"/api/v1/auth/apple/callback?code=mock_apple_code&state={state}",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == f"{settings.FRONTEND_BASE_URL}/"
        session_cookie = resp.cookies.get(settings.SESSION_COOKIE_NAME)
        assert session_cookie is not None


@pytest.mark.asyncio
async def test_expired_password_reset_token_rejected(clean_async_client: AsyncClient) -> None:
    """Password reset token past expires_at must be rejected."""
    ts = datetime.now().timestamp()
    email = f"expired_reset_{ts}@example.com"
    raw_token = f"raw_expired_reset_{ts}"
    token_hash = hash_token(raw_token)

    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password("Password123!"),
            is_active=True,
        )
        db.add(user)
        await db.flush()

        expired_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            # Expired 2 hours ago
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.add(expired_token)
        await db.commit()

    headers = {"X-Gym-CSRF": "1"}
    resp = await clean_async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewValidPassword123!"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "invalid or expired" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_cors_credentials_and_origin(clean_async_client: AsyncClient) -> None:
    """Verify CORS preflight returns credentials allowed for http://localhost:3000."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, X-Gym-CSRF",
    }
    resp = await clean_async_client.options("/api/v1/auth/login", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"
