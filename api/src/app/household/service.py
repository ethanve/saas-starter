"""Household business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.household.models import Household, HouseholdMember, HouseholdMembership, MemberKind

DEFAULT_MEMBER_COLORS = [
    "#2563eb",
    "#db2777",
    "#16a34a",
    "#d97706",
    "#7c3aed",
    "#0891b2",
    "#dc2626",
]


def _initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


async def create_household_for_user(
    session: AsyncSession, user: User, name: str | None = None
) -> Household:
    household = Household(name=name or f"{user.name}'s household")
    session.add(household)
    await session.flush()

    session.add(HouseholdMembership(user_id=user.id, household_id=household.id))

    self_member = HouseholdMember(
        household_id=household.id,
        name=user.name,
        short=_initials(user.name),
        color=DEFAULT_MEMBER_COLORS[0],
        kind=MemberKind.ADULT.value,
        user_id=user.id,
    )
    session.add(self_member)

    await session.flush()
    return household


async def get_household_for_user(
    session: AsyncSession, user: User
) -> Household | None:
    result = await session.execute(
        select(Household)
        .join(HouseholdMembership, HouseholdMembership.household_id == Household.id)
        .where(HouseholdMembership.user_id == user.id)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_members(
    session: AsyncSession, household_id: int, include_deleted: bool = False
) -> list[HouseholdMember]:
    stmt = select(HouseholdMember).where(HouseholdMember.household_id == household_id)
    if not include_deleted:
        stmt = stmt.where(HouseholdMember.deleted_at.is_(None))
    stmt = stmt.order_by(HouseholdMember.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def attach_user_to_household(
    session: AsyncSession,
    user: User,
    household: Household,
    member_public_id: str | None = None,
) -> HouseholdMember:
    """Link a newly-verified user to an existing household.

    If member_public_id is given and matches an unclaimed member, bind the user to it.
    Otherwise create a fresh adult member for the user.
    """
    existing_membership = await session.execute(
        select(HouseholdMembership)
        .where(HouseholdMembership.user_id == user.id)
        .where(HouseholdMembership.household_id == household.id)
    )
    if existing_membership.scalar_one_or_none() is None:
        session.add(HouseholdMembership(user_id=user.id, household_id=household.id))

    if member_public_id:
        result = await session.execute(
            select(HouseholdMember)
            .where(HouseholdMember.public_id == member_public_id)
            .where(HouseholdMember.household_id == household.id)
        )
        member = result.scalar_one_or_none()
        if member is not None:
            member.user_id = user.id
            member.kind = MemberKind.ADULT.value
            await session.flush()
            return member

    member_count_result = await session.execute(
        select(HouseholdMember).where(HouseholdMember.household_id == household.id)
    )
    member_count = len(member_count_result.scalars().all())

    member = HouseholdMember(
        household_id=household.id,
        name=user.name,
        short=_initials(user.name),
        color=DEFAULT_MEMBER_COLORS[member_count % len(DEFAULT_MEMBER_COLORS)],
        kind=MemberKind.ADULT.value,
        user_id=user.id,
    )
    session.add(member)
    await session.flush()
    return member
