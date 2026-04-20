"""Unified sync endpoint — one poll returns all changes since <since>."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.area.models import Area
from app.area.schemas import AreaResponse
from app.auth.models import User
from app.core.database import Session
from app.core.lookups import batch_public_ids
from app.household.dependencies import CurrentHousehold
from app.household.models import HouseholdMember
from app.household.routes import members_to_responses
from app.household.schemas import HouseholdMemberResponse
from app.project.models import Project
from app.project.routes import projects_to_responses
from app.project.schemas import ProjectResponse
from app.task.models import Task, TaskComment
from app.task.routes import tasks_to_responses
from app.task.schemas import CommentResponse, TaskResponse


class SyncResponse(BaseModel):
    server_time: datetime
    members: list[HouseholdMemberResponse]
    areas: list[AreaResponse]
    projects: list[ProjectResponse]
    tasks: list[TaskResponse]
    comments: list[CommentResponse]


router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("", response_model=SyncResponse)
async def sync(
    household: CurrentHousehold,
    session: Session,
    since: Annotated[datetime | None, Query()] = None,
) -> SyncResponse:
    server_time = datetime.now(UTC)

    def _changed_clause(table, since_dt):
        if since_dt is None:
            return None
        if hasattr(table, "deleted_at"):
            return or_(table.updated_at > since_dt, table.deleted_at > since_dt)
        return table.updated_at > since_dt

    stmt = select(HouseholdMember).where(HouseholdMember.household_id == household.id)
    clause = _changed_clause(HouseholdMember, since)
    if clause is not None:
        stmt = stmt.where(clause)
    members = list((await session.execute(stmt)).scalars().all())

    stmt = select(Area).where(Area.household_id == household.id)
    clause = _changed_clause(Area, since)
    if clause is not None:
        stmt = stmt.where(clause)
    areas = list((await session.execute(stmt)).scalars().all())

    stmt = select(Project).where(Project.household_id == household.id)
    clause = _changed_clause(Project, since)
    if clause is not None:
        stmt = stmt.where(clause)
    projects = list((await session.execute(stmt)).scalars().all())

    stmt = select(Task).where(Task.household_id == household.id)
    clause = _changed_clause(Task, since)
    if clause is not None:
        stmt = stmt.where(clause)
    tasks = list((await session.execute(stmt)).scalars().all())

    stmt = (
        select(TaskComment)
        .join(Task, Task.id == TaskComment.task_id)
        .where(Task.household_id == household.id)
    )
    if since is not None:
        stmt = stmt.where(TaskComment.updated_at > since)
    comments = list((await session.execute(stmt)).scalars().all())

    # Batch-resolve comment authors in one query instead of one per comment.
    comment_responses: list[CommentResponse] = []
    if comments:
        author_ids = {c.author_user_id for c in comments}
        authors = await batch_public_ids(session, User, author_ids)
        comment_responses = [
            CommentResponse(
                public_id=c.public_id,
                author_user_public_id=authors[c.author_user_id],
                text=c.text,
                created_at=c.created_at,
            )
            for c in comments
        ]

    return SyncResponse(
        server_time=server_time,
        members=await members_to_responses(session, members),
        areas=[AreaResponse.model_validate(a) for a in areas],
        projects=await projects_to_responses(session, projects),
        tasks=await tasks_to_responses(session, tasks),
        comments=comment_responses,
    )
