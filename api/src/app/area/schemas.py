"""Area schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AreaResponse(BaseModel):
    model_config = {"from_attributes": True}

    public_id: str
    name: str
    color: str
    slug: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CreateAreaRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    color: str = Field(..., min_length=1, max_length=32)
    slug: str = Field(..., min_length=1, max_length=32)


class UpdateAreaRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    color: str | None = Field(None, min_length=1, max_length=32)
    slug: str | None = Field(None, min_length=1, max_length=32)
