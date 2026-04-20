"""Project schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectResponse(BaseModel):
    public_id: str
    name: str
    area_public_id: str
    lead_member_public_id: str
    for_member_public_id: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    area_public_id: str
    lead_member_public_id: str
    for_member_public_id: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    area_public_id: str | None = None
    lead_member_public_id: str | None = None
    for_member_public_id: str | None = None
