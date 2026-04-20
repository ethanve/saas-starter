"""Project routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.area.models import Area
from app.core.database import Session
from app.core.exceptions import NotFoundError, ValidationError
from app.core.lookups import batch_public_ids
from app.household.dependencies import CurrentHousehold
from app.household.models import HouseholdMember
from app.project.models import Project
from app.project.schemas import CreateProjectRequest, ProjectResponse, UpdateProjectRequest

router = APIRouter(prefix="/projects", tags=["projects"])


async def _resolve_area_id(session: AsyncSession, household_id: int, public_id: str) -> int:
    result = await session.execute(
        select(Area.id)
        .where(Area.household_id == household_id)
        .where(Area.public_id == public_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ValidationError(f"Area not found: {public_id}")
    return row


async def _resolve_member_id(
    session: AsyncSession, household_id: int, public_id: str
) -> int:
    result = await session.execute(
        select(HouseholdMember.id)
        .where(HouseholdMember.household_id == household_id)
        .where(HouseholdMember.public_id == public_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ValidationError(f"Member not found: {public_id}")
    return row


def _project_to_response_with_maps(
    project: Project,
    areas: dict[int, str],
    members: dict[int, str],
) -> ProjectResponse:
    return ProjectResponse(
        public_id=project.public_id,
        name=project.name,
        area_public_id=areas[project.area_id],
        lead_member_public_id=members[project.lead_member_id],
        for_member_public_id=(
            members.get(project.for_member_id) if project.for_member_id else None
        ),
        created_at=project.created_at,
        updated_at=project.updated_at,
        deleted_at=project.deleted_at,
    )


async def projects_to_responses(
    session: AsyncSession, projects: list[Project]
) -> list[ProjectResponse]:
    if not projects:
        return []
    area_ids = {p.area_id for p in projects}
    member_ids = {p.lead_member_id for p in projects} | {
        p.for_member_id for p in projects if p.for_member_id is not None
    }
    areas = await batch_public_ids(session, Area, area_ids)
    members = await batch_public_ids(session, HouseholdMember, member_ids)
    return [_project_to_response_with_maps(p, areas, members) for p in projects]


async def _project_to_response(
    session: AsyncSession, project: Project
) -> ProjectResponse:
    responses = await projects_to_responses(session, [project])
    return responses[0]


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    household: CurrentHousehold, session: Session
) -> list[ProjectResponse]:
    result = await session.execute(
        select(Project)
        .where(Project.household_id == household.id)
        .where(Project.deleted_at.is_(None))
        .order_by(Project.created_at)
    )
    return await projects_to_responses(session, list(result.scalars().all()))


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    household: CurrentHousehold,
    session: Session,
) -> ProjectResponse:
    area_id = await _resolve_area_id(session, household.id, body.area_public_id)
    lead_id = await _resolve_member_id(session, household.id, body.lead_member_public_id)
    for_id = (
        await _resolve_member_id(session, household.id, body.for_member_public_id)
        if body.for_member_public_id
        else None
    )
    project = Project(
        household_id=household.id,
        name=body.name,
        area_id=area_id,
        lead_member_id=lead_id,
        for_member_id=for_id,
    )
    session.add(project)
    await session.flush()
    return await _project_to_response(session, project)


async def _load_project(session: Session, household_id: int, public_id: str) -> Project:
    result = await session.execute(
        select(Project)
        .where(Project.household_id == household_id)
        .where(Project.public_id == public_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    household: CurrentHousehold,
    session: Session,
) -> ProjectResponse:
    project = await _load_project(session, household.id, project_id)
    if body.name is not None:
        project.name = body.name
    if body.area_public_id is not None:
        project.area_id = await _resolve_area_id(session, household.id, body.area_public_id)
    if body.lead_member_public_id is not None:
        project.lead_member_id = await _resolve_member_id(
            session, household.id, body.lead_member_public_id
        )
    if body.for_member_public_id is not None:
        project.for_member_id = await _resolve_member_id(
            session, household.id, body.for_member_public_id
        )
    await session.flush()
    return await _project_to_response(session, project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    household: CurrentHousehold,
    session: Session,
) -> None:
    project = await _load_project(session, household.id, project_id)
    project.deleted_at = datetime.now(UTC)
    await session.flush()
