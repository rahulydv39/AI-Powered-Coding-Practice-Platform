"""Automated test suite for social sign-in (Google, GitHub, Apple) and LeetCode profile linking."""

from datetime import datetime
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.user import User, UserOAuthAccount

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
async def test_list_oauth_providers(clean_async_client: AsyncClient) -> None:
    """GET /api/v1/auth/providers returns list of supported providers and configuration status."""
    resp = await clean_async_client.get("/api/v1/auth/providers")
    assert resp.status_code == 200
    providers = resp.json()
    provider_names = [p["provider"] for p in providers]
    assert "google" in provider_names
    assert "github" in provider_names
    assert "apple" in provider_names


@pytest.mark.asyncio
async def test_unconfigured_oauth_provider_returns_descriptive_error(clean_async_client: AsyncClient) -> None:
    """Initiating OAuth when credentials are not configured returns safe, actionable HTTP 400."""
    with patch.object(settings, "GOOGLE_CLIENT_ID", None):
        resp = await clean_async_client.get("/api/v1/auth/google/authorize", follow_redirects=False)
        assert resp.status_code == 400
        assert "not configured" in resp.json()["error"]["message"].lower()

    with patch.object(settings, "GITHUB_CLIENT_ID", None):
        resp = await clean_async_client.get("/api/v1/auth/github/authorize", follow_redirects=False)
        assert resp.status_code == 400
        assert "not configured" in resp.json()["error"]["message"].lower()

    with patch.object(settings, "APPLE_CLIENT_ID", None):
        resp = await clean_async_client.get("/api/v1/auth/apple/authorize", follow_redirects=False)
        assert resp.status_code == 400
        assert "not configured" in resp.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_google_oauth_callback_creates_user_and_session(clean_async_client: AsyncClient) -> None:
    """Mocked successful Google OAuth callback creates user, oauth account, and session cookie."""
    ts = datetime.now().timestamp()
    google_sub = f"google_sub_{int(ts)}"
    google_email = f"google_user_{int(ts)}@example.com"
    state = "valid_test_state_123"

    mock_profile = {
        "provider_account_id": google_sub,
        "email": google_email,
        "full_name": "Google Test Student",
    }

    clean_async_client.cookies.set("oauth_state", state)
    clean_async_client.cookies.set("oauth_verifier", "test_verifier")

    with patch("app.api.v1.endpoints.auth.exchange_google_code", return_value=mock_profile):
        resp = await clean_async_client.get(
            f"/api/v1/auth/google/callback?code=mock_code&state={state}",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == f"{settings.FRONTEND_BASE_URL}/"
        session_cookie = resp.cookies.get(settings.SESSION_COOKIE_NAME)
        assert session_cookie is not None

    # Verify User and UserOAuthAccount in DB
    async with AsyncSessionLocal() as session:
        oauth_rec = await session.scalar(
            select(UserOAuthAccount).where(
                UserOAuthAccount.provider == "google",
                UserOAuthAccount.provider_account_id == google_sub,
            )
        )
        assert oauth_rec is not None
        user_rec = await session.scalar(select(User).where(User.id == oauth_rec.user_id))
        assert user_rec is not None
        assert user_rec.email == google_email.lower()


@pytest.mark.asyncio
async def test_github_oauth_callback_creates_user_and_session(clean_async_client: AsyncClient) -> None:
    """Mocked successful GitHub OAuth callback creates user and session cookie."""
    ts = datetime.now().timestamp()
    github_id = f"github_id_{int(ts)}"
    github_email = f"github_user_{int(ts)}@example.com"
    state = "valid_github_state_456"

    mock_profile = {
        "provider_account_id": github_id,
        "email": github_email,
        "full_name": "Octocat Student",
    }

    clean_async_client.cookies.set("oauth_state", state)

    with patch("app.api.v1.endpoints.auth.exchange_github_code", return_value=mock_profile):
        resp = await clean_async_client.get(
            f"/api/v1/auth/github/callback?code=mock_github_code&state={state}",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == f"{settings.FRONTEND_BASE_URL}/"
        session_cookie = resp.cookies.get(settings.SESSION_COOKIE_NAME)
        assert session_cookie is not None


@pytest.mark.asyncio
async def test_oauth_state_mismatch_rejected(clean_async_client: AsyncClient) -> None:
    """Tampered or missing OAuth state cookie must redirect to login with error."""
    clean_async_client.cookies.set("oauth_state", "expected_state")
    resp = await clean_async_client.get(
        "/api/v1/auth/google/callback?code=test_code&state=forged_state",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]
    assert "error=" in resp.headers["location"]


@pytest.mark.asyncio
async def test_leetcode_status_endpoint(clean_async_client: AsyncClient) -> None:
    """LeetCode status endpoint clarifies why official OAuth sign-in is not supported."""
    resp = await clean_async_client.get("/api/v1/auth/leetcode/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "leetcode"
    assert data["supports_oauth_sign_in"] is False
    assert data["official_auth_supported"] is False
    assert "does not provide an official public third-party oauth" in data["message"].lower()


@pytest.mark.asyncio
async def test_oauth_safe_next_return_url_preservation(clean_async_client: AsyncClient) -> None:
    """OAuth authorize sets oauth_next cookie for local paths and ignores open redirect attempts."""
    with patch.object(settings, "GOOGLE_CLIENT_ID", "mock_id"), patch.object(
        settings, "GOOGLE_CLIENT_SECRET", "mock_secret"
    ):
        # 1. Valid local path
        resp = await clean_async_client.get(
            "/api/v1/auth/google/authorize?next=/challenges/circuit-breaker-pattern",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        cookie_val = resp.cookies.get("oauth_next")
        assert cookie_val is not None
        assert cookie_val.strip('"') == "/challenges/circuit-breaker-pattern"

        # 2. Scheme-relative open redirect attack (//evil.com)
        resp2 = await clean_async_client.get(
            "/api/v1/auth/google/authorize?next=//evil.com/phish",
            follow_redirects=False,
        )
        assert resp2.status_code == 302
        assert "oauth_next" not in resp2.cookies

        # 3. Absolute URL open redirect attack (https://evil.com)
        resp3 = await clean_async_client.get(
            "/api/v1/auth/google/authorize?next=https://evil.com",
            follow_redirects=False,
        )
        assert resp3.status_code == 302
        assert "oauth_next" not in resp3.cookies


@pytest.mark.asyncio
async def test_oauth_callback_redirects_to_saved_next_target(clean_async_client: AsyncClient) -> None:
    """OAuth callback navigates to oauth_next URL and clears the temporary cookie."""
    mock_profile = {
        "provider_account_id": "google_sub_next_123",
        "email": "student_next@example.com",
        "full_name": "Next Student",
    }
    with patch("app.api.v1.endpoints.auth.exchange_google_code", return_value=mock_profile):
        clean_async_client.cookies.set("oauth_state", "valid_state_next")
        clean_async_client.cookies.set("oauth_verifier", "valid_verifier_next")
        clean_async_client.cookies.set("oauth_next", "/challenges/rate-limiter-token-bucket")

        resp = await clean_async_client.get(
            "/api/v1/auth/google/callback?code=mock_code&state=valid_state_next",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == f"{settings.FRONTEND_BASE_URL}/challenges/rate-limiter-token-bucket"
        # Verify oauth_next cookie is deleted on response
        deleted_cookies = [h for h in resp.headers.get_list("set-cookie") if "oauth_next" in h]
        assert any('Max-Age=0' in h or 'expires=' in h.lower() for h in deleted_cookies)

