"""Household schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.household.models import MemberKind


class HouseholdMemberResponse(BaseModel):
    model_config = {"from_attributes": True}

    public_id: str
    name: str
    short: str
    color: str
    kind: MemberKind
    user_public_id: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class HouseholdResponse(BaseModel):
    model_config = {"from_attributes": True}

    public_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    members: list[HouseholdMemberResponse] = []


class UpdateHouseholdRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)


class CreateMemberRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    short: str = Field(..., min_length=1, max_length=8)
    color: str = Field(..., min_length=1, max_length=32)
    kind: MemberKind = MemberKind.ADULT


class UpdateMemberRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    short: str | None = Field(None, min_length=1, max_length=8)
    color: str | None = Field(None, min_length=1, max_length=32)
    kind: MemberKind | None = None


class InviteRequest(BaseModel):
    email: EmailStr
    member_public_id: str | None = None
