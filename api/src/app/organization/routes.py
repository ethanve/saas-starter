"""Organization routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.auth.dependencies import CurrentUser
from app.auth.models import Organization, UserOrganizationMembership
from app.core.database import Session
from app.organization.schemas import (
    CreateOrganizationRequest,
    MemberResponse,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from app.organization.service import (
    create_organization,
    delete_organization,
    list_members,
    update_organization,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrganizationResponse)
async def create_org(
    body: CreateOrganizationRequest,
    user: CurrentUser,
    session: Session,
) -> OrganizationResponse:
    org = await create_organization(session, body.name, user)
    return OrganizationResponse.model_validate(org)


@router.get("", response_model=list[OrganizationResponse])
async def list_orgs(
    user: CurrentUser,
    session: Session,
) -> list[OrganizationResponse]:
    result = await session.execute(
        select(Organization)
        .join(UserOrganizationMembership)
        .where(UserOrganizationMembership.user_id == user.id)
    )
    orgs = result.scalars().all()
    return [OrganizationResponse.model_validate(org) for org in orgs]


@router.get("/{org_slug}", response_model=OrganizationResponse)
async def get_org(
    org_slug: str,
    user: CurrentUser,
    session: Session,
) -> OrganizationResponse:
    result = await session.execute(
        select(Organization)
        .join(UserOrganizationMembership)
        .where(Organization.slug == org_slug)
        .where(UserOrganizationMembership.user_id == user.id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    return OrganizationResponse.model_validate(org)


@router.patch("/{org_slug}", response_model=OrganizationResponse)
async def update_org(
    org_slug: str,
    body: UpdateOrganizationRequest,
    user: CurrentUser,
    session: Session,
) -> OrganizationResponse:
    result = await session.execute(
        select(Organization)
        .join(UserOrganizationMembership)
        .where(Organization.slug == org_slug)
        .where(UserOrganizationMembership.user_id == user.id)
        .where(UserOrganizationMembership.role == "org_admin")
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found or not authorized")
    org = await update_organization(session, org, body.name)
    return OrganizationResponse.model_validate(org)


@router.delete("/{org_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org(
    org_slug: str,
    user: CurrentUser,
    session: Session,
) -> None:
    result = await session.execute(
        select(Organization)
        .join(UserOrganizationMembership)
        .where(Organization.slug == org_slug)
        .where(UserOrganizationMembership.user_id == user.id)
        .where(UserOrganizationMembership.role == "org_admin")
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found or not authorized")
    await delete_organization(session, org)


@router.get("/{org_slug}/members", response_model=list[MemberResponse])
async def list_org_members(
    org_slug: str,
    user: CurrentUser,
    session: Session,
) -> list[MemberResponse]:
    result = await session.execute(
        select(Organization)
        .join(UserOrganizationMembership)
        .where(Organization.slug == org_slug)
        .where(UserOrganizationMembership.user_id == user.id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    members = await list_members(session, org.id)
    return [
        MemberResponse(
            user_id=u.public_id,
            email=u.email,
            name=u.name,
            role=m.role,
            joined_at=m.created_at,
        )
        for m, u in members
    ]
