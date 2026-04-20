"""Task schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.task.models import TaskPriority, TaskStatus


class TaskStep(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    done: bool = False


class TaskResponse(BaseModel):
    public_id: str
    title: str
    notes: str | None = None
    assignee_member_public_id: str | None = None
    project_public_id: str
    area_public_id: str
    due_date: date | None = None
    is_event: bool
    status: TaskStatus
    priority: TaskPriority | None = None
    steps: list[TaskStep]
    created_by_user_public_id: str
    updated_by_user_public_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    assignee_member_public_id: str | None = None
    project_public_id: str
    due_date: date | None = None
    is_event: bool = False
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority | None = None
    steps: list[TaskStep] = Field(default_factory=list)


class UpdateTaskRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    notes: str | None = None
    assignee_member_public_id: str | None = None
    project_public_id: str | None = None
    due_date: date | None = None
    is_event: bool | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    steps: list[TaskStep] | None = None


class CommentResponse(BaseModel):
    public_id: str
    author_user_public_id: str
    text: str
    created_at: datetime


class CreateCommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
