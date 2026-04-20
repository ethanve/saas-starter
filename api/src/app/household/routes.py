"""Household routes."""

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.auth.models import User
from app.core.database import Session
from app.core.exceptions import NotFoundError
from app.core.lookups import batch_public_ids
from app.household.dependencies import CurrentHousehold
from app.household.models import HouseholdMember, MemberKind
from app.household.schemas import (
    CreateMemberRequest,
    HouseholdMemberResponse,
    HouseholdResponse,
    InviteRequest,
    UpdateHouseholdRequest,
    UpdateMemberRequest,
)
from app.household.service import list_members

router = APIRouter(prefix="/household", tags=["household"])


def _member_to_response(
    m: HouseholdMember, user_public_id: str | None = None
) -> HouseholdMemberResponse:
    return HouseholdMemberResponse(
        public_id=m.public_id,
        name=m.name,
        short=m.short,
        color=m.color,
        kind=MemberKind(m.kind),
        user_public_id=user_public_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


async def _build_member_response(
    session: AsyncSession, m: HouseholdMember
) -> HouseholdMemberResponse:
    responses = await members_to_responses(session, [m])
    return responses[0]


async def members_to_responses(
    session: AsyncSession, members: list[HouseholdMember]
) -> list[HouseholdMemberResponse]:
    if not members:
        return []
    user_ids = {m.user_id for m in members if m.user_id is not None}
    users = await batch_public_ids(session, User, user_ids)
    return [
        _member_to_response(m, users.get(m.user_id) if m.user_id else None)
        for m in members
    ]


@router.get("", response_model=HouseholdResponse)
async def get_household(
    household: CurrentHousehold,
    session: Session,
) -> HouseholdResponse:
    members = await list_members(session, household.id)
    return HouseholdResponse(
        public_id=household.public_id,
        name=household.name,
        created_at=household.created_at,
        updated_at=household.updated_at,
        members=await members_to_responses(session, members),
    )


@router.patch("", response_model=HouseholdResponse)
async def update_household(
    body: UpdateHouseholdRequest,
    household: CurrentHousehold,
    session: Session,
) -> HouseholdResponse:
    if body.name is not None:
        household.name = body.name
    await session.flush()
    members = await list_members(session, household.id)
    return HouseholdResponse(
        public_id=household.public_id,
        name=household.name,
        created_at=household.created_at,
        updated_at=household.updated_at,
        members=await members_to_responses(session, members),
    )


@router.post(
    "/members",
    response_model=HouseholdMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_member(
    body: CreateMemberRequest,
    household: CurrentHousehold,
    session: Session,
) -> HouseholdMemberResponse:
    member = HouseholdMember(
        household_id=household.id,
        name=body.name,
        short=body.short,
        color=body.color,
        kind=body.kind.value,
    )
    session.add(member)
    await session.flush()
    return await _build_member_response(session, member)


async def _load_member(session: Session, household_id: int, public_id: str) -> HouseholdMember:
    result = await session.execute(
        select(HouseholdMember)
        .where(HouseholdMember.household_id == household_id)
        .where(HouseholdMember.public_id == public_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotFoundError("Member not found")
    return member


@router.patch("/members/{member_id}", response_model=HouseholdMemberResponse)
async def update_member(
    member_id: str,
    body: UpdateMemberRequest,
    household: CurrentHousehold,
    session: Session,
) -> HouseholdMemberResponse:
    member = await _load_member(session, household.id, member_id)
    if body.name is not None:
        member.name = body.name
    if body.short is not None:
        member.short = body.short
    if body.color is not None:
        member.color = body.color
    if body.kind is not None:
        member.kind = body.kind.value
    await session.flush()
    return await _build_member_response(session, member)


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: str,
    household: CurrentHousehold,
    session: Session,
) -> None:
    from datetime import UTC, datetime

    member = await _load_member(session, household.id, member_id)
    member.deleted_at = datetime.now(UTC)
    await session.flush()


@router.post("/invite", status_code=status.HTTP_202_ACCEPTED)
async def invite(
    body: InviteRequest,
    user: CurrentUser,
    household: CurrentHousehold,
    session: Session,
) -> dict[str, str]:
    from app.auth.magic_link.service import create_magic_link

    if body.member_public_id:
        await _load_member(session, household.id, body.member_public_id)

    await create_magic_link(
        email=body.email,
        household_id=household.id,
        household_name=household.name,
        inviter_name=user.name,
        member_public_id=body.member_public_id,
    )
    return {"message": "Invite sent"}
