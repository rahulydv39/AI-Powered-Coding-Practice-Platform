"""Authentication service managing users, server-managed sessions, and recovery tokens."""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import (
    generate_random_token,
    hash_password,
    hash_token,
    normalize_email,
    validate_email_format,
    validate_password_strength,
    verify_password,
)
from app.models.user import PasswordResetToken, User, UserOAuthAccount, UserSession

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationError(Exception):
    """Raised for authentication credential failures."""


class RegistrationError(Exception):
    """Raised for account creation validation failures."""


class PasswordResetError(Exception):
    """Raised for invalid or expired password recovery tokens."""


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[User, str]:
    """Create a new student account and initiate an authenticated session.
    
    Returns:
        Tuple of (User, raw_session_token)
    """
    clean_email = normalize_email(email)
    if not validate_email_format(clean_email):
        raise RegistrationError("Please provide a valid email address.")

    pw_err = validate_password_strength(password)
    if pw_err:
        raise RegistrationError(pw_err)

    # Check for existing user with this email
    existing_stmt = select(User).where(User.email == clean_email)
    existing_user = (await db.scalars(existing_stmt)).first()

    if existing_user is not None:
        raise RegistrationError("An account with this email address already exists.")

    hashed_pw = hash_password(password)
    new_user = User(
        email=clean_email,
        hashed_password=hashed_pw,
        full_name=full_name.strip() if full_name else None,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    # Create session
    session_rec, raw_session_token = await create_user_session(
        db,
        user_id=new_user.id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    await db.commit()
    await db.refresh(new_user)

    logger.info("Registered new user: %s", new_user.id)
    return new_user, raw_session_token


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[User, str]:
    """Verify credentials and initiate an authenticated session.
    
    Returns:
        Tuple of (User, raw_session_token)
    """
    clean_email = normalize_email(email)
    generic_error = "Invalid email or password."

    stmt = select(User).where(User.email == clean_email)
    user = (await db.scalars(stmt)).first()

    if user is None or not user.hashed_password:
        # User not found or signed up via OAuth without a local password
        raise AuthenticationError(generic_error)

    if not verify_password(password, user.hashed_password):
        raise AuthenticationError(generic_error)

    if not user.is_active:
        raise AuthenticationError("This account is currently deactivated.")

    session_rec, raw_session_token = await create_user_session(
        db,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    await db.commit()
    await db.refresh(user)

    logger.info("User logged in: %s", user.id)
    return user, raw_session_token


async def create_user_session(
    db: AsyncSession,
    user_id: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[UserSession, str]:
    """Create a server-managed session record with a SHA-256 token hash."""
    raw_token = generate_random_token(32)
    token_hash = hash_token(raw_token)
    expires_at = utc_now() + timedelta(seconds=settings.SESSION_COOKIE_MAX_AGE)

    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent[:512] if user_agent else None,
        ip_address=ip_address[:64] if ip_address else None,
    )
    db.add(session)
    await db.flush()
    return session, raw_token


async def authenticate_session(
    db: AsyncSession,
    raw_token: Optional[str],
) -> Optional[User]:
    """Validate raw session token from cookie, checking expiration and revocation."""
    if not raw_token:
        return None

    token_hash = hash_token(raw_token)
    stmt = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now(),
        )
    )
    session_rec = (await db.scalars(stmt)).first()

    if session_rec is None or not session_rec.user or not session_rec.user.is_active:
        return None

    return session_rec.user


async def logout_session(
    db: AsyncSession,
    raw_token: Optional[str],
) -> bool:
    """Revoke an active session token."""
    if not raw_token:
        return False

    token_hash = hash_token(raw_token)
    stmt = (
        update(UserSession)
        .where(UserSession.token_hash == token_hash, UserSession.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount > 0


async def revoke_all_user_sessions(
    db: AsyncSession,
    user_id: str,
) -> int:
    """Revoke all active sessions for a given user (e.g., on password reset)."""
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount


async def request_password_reset(
    db: AsyncSession,
    email: str,
) -> Optional[str]:
    """Create a single-use expiring password recovery token.
    
    Returns raw token if user exists (for mailing or testing), without leaking existence.
    """
    clean_email = normalize_email(email)
    stmt = select(User).where(User.email == clean_email)
    user = (await db.scalars(stmt)).first()

    if user is None:
        return None

    raw_token = generate_random_token(32)
    token_hash = hash_token(raw_token)
    expires_at = utc_now() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.commit()

    logger.info("Password reset token generated for user: %s (expires: %s)", user.id, expires_at)
    return raw_token


async def reset_password_with_token(
    db: AsyncSession,
    raw_token: str,
    new_password: str,
) -> User:
    """Validate reset token, update password, mark token used, and revoke existing sessions."""
    pw_err = validate_password_strength(new_password)
    if pw_err:
        raise PasswordResetError(pw_err)

    token_hash = hash_token(raw_token)
    stmt = (
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > utc_now(),
        )
    )
    token_rec = (await db.scalars(stmt)).first()

    if token_rec is None or not token_rec.user:
        raise PasswordResetError("Invalid or expired password reset token.")

    user = token_rec.user
    user.hashed_password = hash_password(new_password)
    user.updated_at = utc_now()
    token_rec.used_at = utc_now()

    # Revoke all existing sessions for security
    await revoke_all_user_sessions(db, user.id)
    await db.commit()
    await db.refresh(user)

    logger.info("Password successfully reset for user: %s", user.id)
    return user


async def get_linked_oauth_providers(
    db: AsyncSession,
    user_id: str,
) -> List[str]:
    """Return list of external provider names linked to the user account."""
    stmt = select(UserOAuthAccount.provider).where(UserOAuthAccount.user_id == user_id)
    providers = (await db.scalars(stmt)).all()
    return list(providers)
