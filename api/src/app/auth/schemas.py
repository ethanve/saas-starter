"""Auth schemas."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

MIN_PASSWORD_LENGTH = 12


def _validate_password(v: str) -> str:
    if len(v) < MIN_PASSWORD_LENGTH:
        msg = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        raise ValueError(msg)
    if not re.search(r"[a-z]", v):
        msg = "Password must contain at least one lowercase letter"
        raise ValueError(msg)
    if not re.search(r"[A-Z]", v):
        msg = "Password must contain at least one uppercase letter"
        raise ValueError(msg)
    if not re.search(r"\d", v):
        msg = "Password must contain at least one digit"
        raise ValueError(msg)
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", v):
        msg = "Password must contain at least one special character"
        raise ValueError(msg)
    return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CookieTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        return _validate_password(v)


class UserResponse(BaseModel):
    public_id: str
    email: str
    name: str
    avatar_url: str | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
