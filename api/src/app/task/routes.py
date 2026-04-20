"""Task routes."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.area.models import Area
from app.auth.dependencies import CurrentUser
from app.auth.models import User
from app.core.database import Session
from app.core.exceptions import NotFoundError, ValidationError
from app.core.lookups import batch_public_ids
from app.household.dependencies import CurrentHousehold
from app.household.models import HouseholdMember
from app.project.models import Project
from app.task.models import Task, TaskComment
from app.task.schemas import (
    CommentResponse,
    CreateCommentRequest,
    CreateTaskRequest,
    TaskResponse,
    TaskStep,
    UpdateTaskRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _member_id_for(
    session: AsyncSession, household_id: int, public_id: str | None
) -> int | None:
    if public_id is None:
        return None
    result = await session.execute(
        select(HouseholdMember.id)
        .where(HouseholdMember.household_id == household_id)
        .where(HouseholdMember.public_id == public_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ValidationError(f"Member not found: {public_id}")
    return row


async def _project_and_area_for(
    session: AsyncSession, household_id: int, project_public_id: str
) -> tuple[int, int]:
    result = await session.execute(
        select(Project.id, Project.area_id)
        .where(Project.household_id == household_id)
        .where(Project.public_id == project_public_id)
    )
    row = result.one_or_none()
    if row is None:
        raise ValidationError(f"Project not found: {project_public_id}")
    return row[0], row[1]


def _task_to_response_with_maps(
    task: Task,
    projects: dict[int, str],
    areas: dict[int, str],
    members: dict[int, str],
    users: dict[int, str],
) -> TaskResponse:
    return TaskResponse(
        public_id=task.public_id,
        title=task.title,
        notes=task.notes,
        assignee_member_public_id=(
            members.get(task.assignee_member_id) if task.assignee_member_id else None
        ),
        project_public_id=projects[task.project_id],
        area_public_id=areas[task.area_id],
        due_date=task.due_date,
        is_event=task.is_event,
        status=task.status,
        priority=task.priority,
        steps=[TaskStep(**s) for s in (task.steps or [])],
        created_by_user_public_id=users[task.created_by_user_id],
        updated_by_user_public_id=users[task.updated_by_user_id],
        created_at=task.created_at,
        updated_at=task.updated_at,
        deleted_at=task.deleted_at,
    )


async def tasks_to_responses(
    session: AsyncSession, tasks: list[Task]
) -> list[TaskResponse]:
    if not tasks:
        return []

    project_ids = {t.project_id for t in tasks}
    area_ids = {t.area_id for t in tasks}
    member_ids = {t.assignee_member_id for t in tasks if t.assignee_member_id is not None}
    user_ids = {t.created_by_user_id for t in tasks} | {t.updated_by_user_id for t in tasks}

    projects = await batch_public_ids(session, Project, project_ids)
    areas = await batch_public_ids(session, Area, area_ids)
    members = await batch_public_ids(session, HouseholdMember, member_ids)
    users = await batch_public_ids(session, User, user_ids)

    return [_task_to_response_with_maps(t, projects, areas, members, users) for t in tasks]


async def task_to_response(session: AsyncSession, task: Task) -> TaskResponse:
    """Single-task convenience wrapper — still just one query per referenced table."""
    responses = await tasks_to_responses(session, [task])
    return responses[0]


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    household: CurrentHousehold,
    session: Session,
    updated_since: Annotated[datetime | None, Query()] = None,
    include_deleted: Annotated[bool, Query()] = False,
) -> list[TaskResponse]:
    stmt = select(Task).where(Task.household_id == household.id)
    if not include_deleted:
        stmt = stmt.where(Task.deleted_at.is_(None))
    if updated_since is not None:
        stmt = stmt.where(Task.updated_at > updated_since)
    stmt = stmt.order_by(Task.created_at)
    result = await session.execute(stmt)
    return await tasks_to_responses(session, list(result.scalars().all()))


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: CreateTaskRequest,
    user: CurrentUser,
    household: CurrentHousehold,
    session: Session,
) -> TaskResponse:
    project_id, area_id = await _project_and_area_for(
        session, household.id, body.project_public_id
    )
    assignee_id = await _member_id_for(session, household.id, body.assignee_member_public_id)

    task = Task(
        household_id=household.id,
        title=body.title,
        notes=body.notes,
        assignee_member_id=assignee_id,
        project_id=project_id,
        area_id=area_id,
        due_date=body.due_date,
        is_event=body.is_event,
        status=body.status.value,
        priority=body.priority.value if body.priority else None,
        steps=[s.model_dump() for s in body.steps],
        created_by_user_id=user.id,
        updated_by_user_id=user.id,
    )
    session.add(task)
    await session.flush()
    return await task_to_response(session, task)


async def _load_task(session: Session, household_id: int, public_id: str) -> Task:
    result = await session.execute(
        select(Task)
        .where(Task.household_id == household_id)
        .where(Task.public_id == public_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    user: CurrentUser,
    household: CurrentHousehold,
    session: Session,
) -> TaskResponse:
    task = await _load_task(session, household.id, task_id)

    if body.title is not None:
        task.title = body.title
    if body.notes is not None:
        task.notes = body.notes
    if body.assignee_member_public_id is not None:
        task.assignee_member_id = await _member_id_for(
            session, household.id, body.assignee_member_public_id
        )
    if body.project_public_id is not None:
        project_id, area_id = await _project_and_area_for(
            session, household.id, body.project_public_id
        )
        task.project_id = project_id
        task.area_id = area_id
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.is_event is not None:
        task.is_event = body.is_event
    if body.status is not None:
        task.status = body.status.value
    if body.priority is not None:
        task.priority = body.priority.value
    if body.steps is not None:
        task.steps = [s.model_dump() for s in body.steps]

    task.updated_by_user_id = user.id
    await session.flush()
    return await task_to_response(session, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    household: CurrentHousehold,
    session: Session,
) -> None:
    task = await _load_task(session, household.id, task_id)
    task.deleted_at = datetime.now(UTC)
    await session.flush()


async def _comments_to_responses(
    session: AsyncSession, comments: list[TaskComment]
) -> list[CommentResponse]:
    if not comments:
        return []
    user_ids = {c.author_user_id for c in comments}
    users = await batch_public_ids(session, User, user_ids)
    return [
        CommentResponse(
            public_id=c.public_id,
            author_user_public_id=users[c.author_user_id],
            text=c.text,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    task_id: str,
    household: CurrentHousehold,
    session: Session,
) -> list[CommentResponse]:
    task = await _load_task(session, household.id, task_id)
    result = await session.execute(
        select(TaskComment)
        .where(TaskComment.task_id == task.id)
        .order_by(TaskComment.created_at)
    )
    return await _comments_to_responses(session, list(result.scalars().all()))


@router.post(
    "/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    task_id: str,
    body: CreateCommentRequest,
    user: CurrentUser,
    household: CurrentHousehold,
    session: Session,
) -> CommentResponse:
    task = await _load_task(session, household.id, task_id)
    comment = TaskComment(task_id=task.id, author_user_id=user.id, text=body.text)
    session.add(comment)
    await session.flush()
    return CommentResponse(
        public_id=comment.public_id,
        author_user_public_id=user.public_id,
        text=comment.text,
        created_at=comment.created_at,
    )
