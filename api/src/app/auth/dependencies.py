"""Auth dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth.cookies import get_access_token_from_cookie
from app.auth.jwt import verify_token
from app.auth.models import Organization, User, UserOrganizationMembership
from app.core.database import Session
from app.core.exceptions import AuthenticationError, AuthorizationError

security = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str:
    if credentials is not None:
        return credentials.credentials

    cookie_token = get_access_token_from_cookie(request)
    if cookie_token is not None:
        return cookie_token

    raise AuthenticationError("Not authenticated")


async def get_current_user(
    request: Request,
    session: Session,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    token = _extract_bearer_token(credentials, request)

    try:
        token_data = verify_token(token)
    except ValueError as e:
        raise AuthenticationError(str(e)) from e

    if token_data.type != "access":
        raise AuthenticationError("Access token required")

    result = await session.execute(select(User).where(User.public_id == token_data.sub))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthorizationError("User account is inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_with_org(
    request: Request,
    session: Session,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> tuple[User, Organization]:
    user = await get_current_user(request, session, credentials)

    membership_result = await session.execute(
        select(UserOrganizationMembership)
        .where(UserOrganizationMembership.user_id == user.id)
        .options(selectinload(UserOrganizationMembership.organization))
        .limit(1)
    )
    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise AuthorizationError("User has no organization membership")

    return user, membership.organization


CurrentUserWithOrg = Annotated[tuple[User, Organization], Depends(get_current_user_with_org)]
