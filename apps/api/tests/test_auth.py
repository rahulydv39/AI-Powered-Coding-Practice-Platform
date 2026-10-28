"""Automated test suite for custom authentication, session management, and password recovery."""

from datetime import datetime
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_token
from app.main import app
from app.models.user import PasswordResetToken

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
async def test_register_success_flow(clean_async_client: AsyncClient) -> None:
    """Registering a new account creates user in DB and establishes an HttpOnly session cookie."""
    unique_email = f"student_{datetime.now().timestamp()}@example.com"
    payload = {
        "email": unique_email,
        "password": "StrongPassword123!",
        "full_name": "New Student",
    }
    headers = {"X-Gym-CSRF": "1"}

    resp = await clean_async_client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["email"] == unique_email.lower()
    assert data["full_name"] == "New Student"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data

    cookie = resp.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie is not None


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(clean_async_client: AsyncClient) -> None:
    """Registering with an already registered email must return HTTP 400."""
    email = f"dup_{datetime.now().timestamp()}@example.com"
    payload = {"email": email, "password": "Password123!"}
    headers = {"X-Gym-CSRF": "1"}

    resp1 = await clean_async_client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = await clean_async_client.post("/api/v1/auth/register", json=payload, headers=headers)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_invalid_inputs(clean_async_client: AsyncClient) -> None:
    """Invalid email formats or weak passwords must be rejected."""
    headers = {"X-Gym-CSRF": "1"}

    # Short password (< 8 chars)
    resp_short = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
        headers=headers,
    )
    assert resp_short.status_code in (400, 422)

    # Invalid email format
    resp_email = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "ValidPassword123!"},
        headers=headers,
    )
    assert resp_email.status_code in (400, 422)


@pytest.mark.asyncio
async def test_login_success_and_logout(clean_async_client: AsyncClient) -> None:
    """Successful login establishes session; logout revokes session and clears cookie."""
    email = f"login_test_{datetime.now().timestamp()}@example.com"
    password = "CorrectPassword123!"
    headers = {"X-Gym-CSRF": "1"}

    # 1. Register account
    await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
        headers=headers,
    )

    # 2. Login
    login_resp = await clean_async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers=headers,
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["email"] == email.lower()
    session_cookie = login_resp.cookies.get(settings.SESSION_COOKIE_NAME)
    assert session_cookie is not None

    # 3. Access protected /me
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, session_cookie)
    me_resp = await clean_async_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email.lower()

    # 4. Logout
    logout_resp = await clean_async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # 5. Verify session revoked on subsequent request
    clean_async_client.cookies.set(settings.SESSION_COOKIE_NAME, session_cookie)
    me_after_logout = await clean_async_client.get("/api/v1/auth/me")
    assert me_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_generic_error(clean_async_client: AsyncClient) -> None:
    """Non-existent email and wrong password both return safe generic 401 error."""
    headers = {"X-Gym-CSRF": "1"}

    # Nonexistent user
    resp_no_user = await clean_async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_user_xyz@example.com", "password": "Password123!"},
        headers=headers,
    )
    assert resp_no_user.status_code == 401
    assert "invalid email or password" in resp_no_user.json()["error"]["message"].lower()

    # Wrong password for existing user
    email = f"wrong_pw_{datetime.now().timestamp()}@example.com"
    await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "RealPassword123!"},
        headers=headers,
    )

    resp_wrong_pw = await clean_async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
        headers=headers,
    )
    assert resp_wrong_pw.status_code == 401
    assert "invalid email or password" in resp_wrong_pw.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_password_reset_flow(clean_async_client: AsyncClient) -> None:
    """Password reset request creates expiring single-use token; resetting invalidates token and updates hash."""
    email = f"reset_test_{datetime.now().timestamp()}@example.com"
    old_password = "OldPassword123!"
    new_password = "BrandNewPassword123!"
    headers = {"X-Gym-CSRF": "1"}

    # 1. Register account
    reg_resp = await clean_async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password},
        headers=headers,
    )
    user_id = reg_resp.json()["id"]

    # 2. Request password reset
    forgot_resp = await clean_async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
        headers=headers,
    )
    assert forgot_resp.status_code == 200
    assert forgot_resp.json()["success"] is True

    # Retrieve created token from DB directly for testing
    test_raw_token = f"test_raw_reset_token_{datetime.now().timestamp()}"
    async with AsyncSessionLocal() as session:
        token_stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
            .order_by(PasswordResetToken.created_at.desc())
        )
        token_rec = (await session.scalars(token_stmt)).first()
        assert token_rec is not None
        token_rec.token_hash = hash_token(test_raw_token)
        await session.commit()

    # 3. Complete password reset using raw token
    reset_resp = await clean_async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": test_raw_token, "new_password": new_password},
        headers=headers,
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # 4. Attempting to use the SAME token a second time must fail (single-use)
    reuse_resp = await clean_async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": test_raw_token, "new_password": "AnotherPassword123!"},
        headers=headers,
    )
    assert reuse_resp.status_code == 400
    assert "invalid or expired" in reuse_resp.json()["error"]["message"].lower()

    # 5. Login with old password fails
    fail_login = await clean_async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
        headers=headers,
    )
    assert fail_login.status_code == 401

    # 6. Login with new password succeeds
    success_login = await clean_async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
        headers=headers,
    )
    assert success_login.status_code == 200
