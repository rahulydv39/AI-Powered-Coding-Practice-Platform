"""Pydantic schemas for authentication and user accounts."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """Payload for creating a new student account."""

    email: str = Field(..., description="Student email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password (min 8 chars)")
    full_name: Optional[str] = Field(None, max_length=255, description="Student full name")


class UserLoginRequest(BaseModel):
    """Payload for email/password authentication."""

    email: str = Field(..., description="Student email address")
    password: str = Field(..., description="Account password")


class ForgotPasswordRequest(BaseModel):
    """Payload for requesting a password reset email."""

    email: str = Field(..., description="Registered account email address")


class ResetPasswordRequest(BaseModel):
    """Payload for completing password reset using a token."""

    token: str = Field(..., description="Single-use password recovery token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New account password (min 8 chars)")


class UserResponse(BaseModel):
    """Safe public user profile model (never leaks password hashes)."""

    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    linked_providers: List[str] = Field(default_factory=list, description="External OAuth providers linked to this account")

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    """Standard message response for auth operations."""

    message: str
    success: bool = True


class OAuthProviderStatus(BaseModel):
    """Status indicating whether an external OAuth provider is configured."""

    provider: str
    configured: bool
    name: str
