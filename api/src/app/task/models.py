"""Task and TaskComment models."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import BaseModel, HouseholdScopedBaseModel, PublicIDMixin


class TaskStatus(StrEnum):
    TODO = "todo"
    DOING = "doing"
    BLOCKED = "blocked"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MED = "med"
    HIGH = "high"
    URGENT = "urgent"


class Task(HouseholdScopedBaseModel, PublicIDMixin):
    __tablename__ = "app_tasks"
    _public_id_prefix = "task_"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignee_member_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_household_members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_areas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    is_event: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(16), default=TaskStatus.TODO.value, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_users.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_users.id", ondelete="RESTRICT"), nullable=False
    )

    steps: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class TaskComment(BaseModel, PublicIDMixin):
    __tablename__ = "app_task_comments"
    _public_id_prefix = "cmt_"

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_users.id", ondelete="RESTRICT"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
