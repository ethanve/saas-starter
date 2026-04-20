"""Area routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import select

from app.area.models import Area
from app.area.schemas import AreaResponse, CreateAreaRequest, UpdateAreaRequest
from app.core.database import Session
from app.core.exceptions import NotFoundError
from app.household.dependencies import CurrentHousehold

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("", response_model=list[AreaResponse])
async def list_areas(household: CurrentHousehold, session: Session) -> list[AreaResponse]:
    result = await session.execute(
        select(Area)
        .where(Area.household_id == household.id)
        .where(Area.deleted_at.is_(None))
        .order_by(Area.created_at)
    )
    return [AreaResponse.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
async def create_area(
    body: CreateAreaRequest,
    household: CurrentHousehold,
    session: Session,
) -> AreaResponse:
    area = Area(
        household_id=household.id,
        name=body.name,
        color=body.color,
        slug=body.slug,
    )
    session.add(area)
    await session.flush()
    return AreaResponse.model_validate(area)


async def _load_area(session: Session, household_id: int, public_id: str) -> Area:
    result = await session.execute(
        select(Area)
        .where(Area.household_id == household_id)
        .where(Area.public_id == public_id)
    )
    area = result.scalar_one_or_none()
    if area is None:
        raise NotFoundError("Area not found")
    return area


@router.patch("/{area_id}", response_model=AreaResponse)
async def update_area(
    area_id: str,
    body: UpdateAreaRequest,
    household: CurrentHousehold,
    session: Session,
) -> AreaResponse:
    area = await _load_area(session, household.id, area_id)
    if body.name is not None:
        area.name = body.name
    if body.color is not None:
        area.color = body.color
    if body.slug is not None:
        area.slug = body.slug
    await session.flush()
    return AreaResponse.model_validate(area)


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(
    area_id: str,
    household: CurrentHousehold,
    session: Session,
) -> None:
    area = await _load_area(session, household.id, area_id)
    area.deleted_at = datetime.now(UTC)
    await session.flush()
