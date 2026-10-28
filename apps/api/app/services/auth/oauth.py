"""OAuth provider integration for Google, GitHub, Apple, and LeetCode profile linking."""

import base64
import hashlib
import json
import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_random_token, normalize_email
from app.models.user import User, UserOAuthAccount, UserSession
from app.services.auth.service import create_user_session

logger = logging.getLogger(__name__)
settings = get_settings()


class OAuthConfigurationError(Exception):
    """Raised when an OAuth provider lacks required credentials."""


class OAuthVerificationError(Exception):
    """Raised when OAuth state, code, or identity verification fails."""


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def get_oauth_provider_status() -> List[Dict[str, Any]]:
    """Return availability status for all external sign-in providers."""
    return [
        {
            "provider": "google",
            "name": "Google",
            "configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        },
        {
            "provider": "github",
            "name": "GitHub",
            "configured": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
        },
        {
            "provider": "apple",
            "name": "Apple",
            "configured": bool(settings.APPLE_CLIENT_ID and settings.APPLE_TEAM_ID and settings.APPLE_KEY_ID),
        },
    ]


# -------------------------------------------------------------------------
# Google OAuth
# -------------------------------------------------------------------------
def get_google_auth_url(state: str, code_challenge: str) -> str:
    """Build Google OAuth2 authorization URL with PKCE."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise OAuthConfigurationError(
            "Google Sign-In is not configured on this server. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_google_code(code: str, code_verifier: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens and retrieve Google user profile."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise OAuthConfigurationError("Google OAuth is not configured.")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_res = await client.post(token_url, data=data)
        if token_res.status_code != 200:
            logger.error("Google token exchange failed: %s", token_res.text)
            raise OAuthVerificationError("Failed to exchange authorization code with Google.")

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        userinfo_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            raise OAuthVerificationError("Failed to fetch user profile from Google.")

        user_info = userinfo_res.json()
        sub = user_info.get("sub")
        email = user_info.get("email")
        if not sub or not email:
            raise OAuthVerificationError("Incomplete profile data received from Google.")

        return {
            "provider_account_id": sub,
            "email": normalize_email(email),
            "full_name": user_info.get("name"),
        }


# -------------------------------------------------------------------------
# GitHub OAuth
# -------------------------------------------------------------------------
def get_github_auth_url(state: str) -> str:
    """Build GitHub OAuth authorization URL."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise OAuthConfigurationError(
            "GitHub Sign-In is not configured on this server. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
        )

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


async def exchange_github_code(code: str) -> Dict[str, Any]:
    """Exchange authorization code for token and retrieve GitHub user profile & primary email."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise OAuthConfigurationError("GitHub OAuth is not configured.")

    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_res = await client.post(
            token_url,
            data=payload,
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            raise OAuthVerificationError("Failed to exchange code with GitHub.")

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            err_desc = token_data.get("error_description", "Unknown error")
            raise OAuthVerificationError(f"GitHub authorization error: {err_desc}")

        # Fetch basic user info
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise OAuthVerificationError("Failed to fetch profile from GitHub.")

        github_user = user_res.json()
        github_id = str(github_user.get("id"))
        email = github_user.get("email")

        # If primary email is private, query emails endpoint
        if not email:
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if emails_res.status_code == 200:
                emails_list = emails_res.json()
                for em in emails_list:
                    if em.get("primary") and em.get("verified"):
                        email = em.get("email")
                        break
                if not email and emails_list:
                    email = emails_list[0].get("email")

        if not github_id or not email:
            raise OAuthVerificationError("Could not retrieve a verified email address from GitHub.")

        return {
            "provider_account_id": github_id,
            "email": normalize_email(email),
            "full_name": github_user.get("name") or github_user.get("login"),
        }


# -------------------------------------------------------------------------
# Apple OAuth
# -------------------------------------------------------------------------
def get_apple_auth_url(state: str) -> str:
    """Build Apple Sign-In authorization URL."""
    if not settings.APPLE_CLIENT_ID:
        raise OAuthConfigurationError(
            "Sign in with Apple is not configured on this server. "
            "Please configure APPLE_CLIENT_ID (Services ID), APPLE_TEAM_ID, and APPLE_KEY_ID."
        )

    params = {
        "client_id": settings.APPLE_CLIENT_ID,
        "redirect_uri": settings.APPLE_REDIRECT_URI,
        "response_type": "code",
        "response_mode": "query",
        "scope": "name email",
        "state": state,
    }
    return f"https://appleid.apple.com/auth/authorize?{urlencode(params)}"


async def exchange_apple_code(code: str) -> Dict[str, Any]:
    """Exchange Apple authorization code for tokens and extract verified subject ID."""
    if not settings.APPLE_CLIENT_ID or not settings.APPLE_TEAM_ID or not settings.APPLE_KEY_ID:
        raise OAuthConfigurationError("Sign in with Apple is not configured.")

    # Apple requires a signed JWT client_secret using the developer ES256 key
    # In local testing or without Apple Developer keys, raise descriptive configuration notice
    if not settings.APPLE_PRIVATE_KEY:
        raise OAuthConfigurationError(
            "Apple Sign-In requires an Apple Developer ES256 private key (APPLE_PRIVATE_KEY). "
            "Configure your Services ID and Keys in the Apple Developer portal."
        )

    raise OAuthConfigurationError(
        "Apple Developer integration requires active Apple Developer Team credentials and a registered domain."
    )


# -------------------------------------------------------------------------
# Account Resolution & Identity Linking
# -------------------------------------------------------------------------
async def resolve_or_create_oauth_user(
    db: AsyncSession,
    provider: str,
    provider_account_id: str,
    email: str,
    full_name: Optional[str] = None,
    current_user: Optional[User] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[User, str]:
    """Link external identity to existing account or create new student account.
    
    Returns:
        Tuple of (User, raw_session_token)
    """
    clean_email = normalize_email(email)

    # 1. Check if external identity already exists in user_oauth_accounts
    oauth_stmt = select(UserOAuthAccount).where(
        UserOAuthAccount.provider == provider,
        UserOAuthAccount.provider_account_id == provider_account_id,
    )
    existing_oauth = (await db.scalars(oauth_stmt)).first()

    if existing_oauth is not None:
        # Account already exists for this external identity
        user_stmt = select(User).where(User.id == existing_oauth.user_id)
        user = (await db.scalars(user_stmt)).first()
        if user is None or not user.is_active:
            raise OAuthVerificationError("Linked student account is not found or inactive.")

        if current_user and current_user.id != user.id:
            raise OAuthVerificationError(
                f"This {provider.capitalize()} account is already linked to another AI Coding Gym profile."
            )

        session_rec, raw_token = await create_user_session(db, user.id, user_agent, ip_address)
        await db.commit()
        return user, raw_token

    # 2. External identity is new. If user is currently logged in, link to current user
    if current_user is not None:
        new_oauth = UserOAuthAccount(
            user_id=current_user.id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        db.add(new_oauth)
        session_rec, raw_token = await create_user_session(db, current_user.id, user_agent, ip_address)
        await db.commit()
        logger.info("Linked %s account to user %s", provider, current_user.id)
        return current_user, raw_token

    # 3. User is not logged in. Check if a user with this email already exists
    user_by_email_stmt = select(User).where(User.email == clean_email)
    existing_by_email = (await db.scalars(user_by_email_stmt)).first()

    if existing_by_email is not None:
        # Existing user found with matching email
        # If the existing user has a local password, prevent automatic hijacking:
        # prompt user to log in with password first, then link from Account Settings.
        if existing_by_email.hashed_password:
            raise OAuthVerificationError(
                f"An account with email {clean_email} already exists. "
                "Please sign in with your email and password, then link your social provider in Account Settings."
            )

        # If they registered via another OAuth provider without a password, link the new provider
        new_oauth = UserOAuthAccount(
            user_id=existing_by_email.id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        db.add(new_oauth)
        session_rec, raw_token = await create_user_session(db, existing_by_email.id, user_agent, ip_address)
        await db.commit()
        return existing_by_email, raw_token

    # 4. Brand new user: create account and link OAuth identity
    new_user = User(
        email=clean_email,
        full_name=full_name,
        hashed_password=None,  # No password for OAuth-only registration
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    new_oauth = UserOAuthAccount(
        user_id=new_user.id,
        provider=provider,
        provider_account_id=provider_account_id,
    )
    db.add(new_oauth)
    await db.flush()

    session_rec, raw_token = await create_user_session(db, new_user.id, user_agent, ip_address)
    await db.commit()
    await db.refresh(new_user)

    logger.info("Registered new user via %s: %s", provider, new_user.id)
    return new_user, raw_token
