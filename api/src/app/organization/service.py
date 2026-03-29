"""Organization business logic."""

import re
import secrets

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Organization, User, UserOrganizationMembership


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


async def generate_unique_slug(session: AsyncSession, name: str) -> str:
    base_slug = slugify(name)
    if not base_slug:
        base_slug = "org"

    slug = base_slug
    exists = await session.scalar(
        select(func.count()).select_from(Organization).where(Organization.slug == slug)
    )
    if not exists:
        return slug

    suffix = secrets.token_hex(3)
    return f"{base_slug}-{suffix}"


async def create_organization(
    session: AsyncSession,
    name: str,
    creator: User,
) -> Organization:
    slug = await generate_unique_slug(session, name)

    org = Organization(name=name, slug=slug)
    session.add(org)
    await session.flush()

    membership = UserOrganizationMembership(
        user_id=creator.id,
        organization_id=org.id,
        role="org_admin",
    )
    session.add(membership)
    await session.flush()

    logger.info(
        "Organization created: org_id={oid}, slug={slug}, creator={uid}",
        oid=org.id,
        slug=slug,
        uid=creator.id,
    )
    return org


async def update_organization(
    session: AsyncSession,
    org: Organization,
    name: str | None,
) -> Organization:
    if name is not None and name != org.name:
        org.name = name
        org.slug = await generate_unique_slug(session, name)
    await session.flush()
    return org


async def delete_organization(session: AsyncSession, org: Organization) -> None:
    await session.delete(org)


async def list_members(
    session: AsyncSession,
    org_id: int,
) -> list[tuple[UserOrganizationMembership, User]]:
    result = await session.execute(
        select(UserOrganizationMembership)
        .where(UserOrganizationMembership.organization_id == org_id)
        .options(selectinload(UserOrganizationMembership.user))
    )
    memberships = result.scalars().all()
    return [(m, m.user) for m in memberships]
