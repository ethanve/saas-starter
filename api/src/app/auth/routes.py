"""Auth API routes — token refresh, logout, profile. Login is via magic link only."""

from datetime import timedelta

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.auth.cookies import clear_auth_cookies, get_refresh_token_from_cookie, set_auth_cookies
from app.auth.dependencies import CurrentUser
from app.auth.jwt import create_access_token
from app.auth.models import RefreshToken, User
from app.auth.schemas import (
    CookieTokenResponse,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.auth.service import create_refresh_token, hash_token
from app.core.config import settings
from app.core.database import Session
from app.core.exceptions import AuthenticationError, AuthorizationError

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_MAX_AGE = settings.api.access_token_expire_minutes * 60
_REFRESH_MAX_AGE = settings.api.refresh_token_expire_days * 86400


async def issue_token_pair(session: Session, user: User) -> TokenResponse:
    access_token = create_access_token(
        data={"sub": user.public_id, "type": "access"},
        expires_delta=timedelta(minutes=settings.api.access_token_expire_minutes),
    )
    refresh_token_string, _ = await create_refresh_token(session, user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_string,
        token_type="bearer",
        expires_in=settings.api.access_token_expire_minutes * 60,
    )


def set_cookies_on_response(
    response: Response,
    token_response: TokenResponse,
) -> CookieTokenResponse:
    csrf_token = set_auth_cookies(
        response,
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        access_max_age=_ACCESS_MAX_AGE,
        refresh_max_age=_REFRESH_MAX_AGE,
    )
    return CookieTokenResponse(
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
        csrf_token=csrf_token,
    )


@router.post("/refresh", response_model=CookieTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    session: Session,
    body: RefreshRequest | None = None,
) -> CookieTokenResponse:
    refresh_token_value = (body.refresh_token if body else None) or get_refresh_token_from_cookie(
        request
    )
    if not refresh_token_value:
        raise AuthenticationError("No refresh token provided")

    token_hash = hash_token(refresh_token_value)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    old_token = result.scalar_one_or_none()

    if not old_token or not old_token.is_valid():
        raise AuthenticationError("Invalid or expired refresh token")

    user_result = await session.execute(select(User).where(User.id == old_token.user_id))
    user = user_result.scalar_one()

    if not user.is_active:
        raise AuthorizationError("User account is inactive")

    old_token.revoked = True
    token_pair = await issue_token_pair(session, user)
    return set_cookies_on_response(response, token_pair)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: Session,
    body: LogoutRequest | None = None,
) -> dict[str, str]:
    refresh_token_value = (body.refresh_token if body else None) or get_refresh_token_from_cookie(
        request
    )
    if refresh_token_value:
        token_hash = hash_token(refresh_token_value)
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        refresh_token = result.scalar_one_or_none()
        if refresh_token:
            refresh_token.revoked = True

    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser) -> UserResponse:
    return UserResponse(
        public_id=user.public_id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    user: CurrentUser,
    session: Session,
) -> UserResponse:
    if body.name is not None:
        user.name = body.name
    await session.flush()
    return UserResponse(
        public_id=user.public_id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        created_at=user.created_at,
    )
