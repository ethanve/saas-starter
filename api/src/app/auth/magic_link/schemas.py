"""Magic-link auth schemas."""

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(None, min_length=1, max_length=255)


class MagicLinkVerifyRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=256)
