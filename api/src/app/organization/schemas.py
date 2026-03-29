"""Organization request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateOrganizationRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = {"from_attributes": True}

    public_id: str
    slug: str
    name: str
    created_at: datetime


class MemberResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    joined_at: datetime
