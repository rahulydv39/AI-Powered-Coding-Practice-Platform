"""Cryptographic security utilities: Argon2id password hashing, token hashing, and normalization."""

import hashlib
import re
import secrets
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

# Initialize Argon2id password hasher with secure defaults
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # 19 MiB
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored Argon2id hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception:
        return False


def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of a session or reset token for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    """Normalize email address to lowercase and strip whitespace."""
    return email.strip().lower()


def validate_password_strength(password: str) -> Optional[str]:
    """Validate password strength rules."""
    if len(password) < 8:
        return "Password must be at least 8 characters in length."
    if len(password) > 128:
        return "Password must not exceed 128 characters."
    return None


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email_format(email: str) -> bool:
    """Validate email address format."""
    return bool(EMAIL_REGEX.match(email))
