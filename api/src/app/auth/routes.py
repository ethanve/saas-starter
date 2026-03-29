"""Auth API routes — login, signup, token refresh, profile."""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.auth.cookies import clear_auth_cookies, get_refresh_token_from_cookie, set_auth_cookies
from app.auth.dependencies import CurrentUser
from app.auth.jwt import create_access_token
from app.auth.models import Organization, RefreshToken, User, UserOrganizationMembership
from app.auth.password import hash_password, verify_password
from app.auth.schemas import (
    CookieTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.auth.service import create_refresh_token, hash_token
from app.core.config import settings
from app.core.database import Session

_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-attack-prevention")

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_MAX_AGE = settings.api.access_token_expire_minutes * 60
_REFRESH_MAX_AGE = settings.api.refresh_token_expire_days * 86400


async def _issue_token_pair(session: Session, user: User) -> TokenResponse:
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


def _set_cookies_on_response(
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


@router.post("/login", response_model=CookieTokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: Session,
) -> CookieTokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        verify_password(body.password, _DUMMY_PASSWORD_HASH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    if user.is_locked():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is locked. Try again later.")

    if not verify_password(body.password, user.password_hash):
        user.increment_failed_attempts()
        if user.failed_login_attempts >= settings.auth.max_failed_login_attempts:
            user.lock_account(
                settings.auth.lockout_base_duration_minutes,
                settings.auth.lockout_max_duration_minutes,
            )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User account is inactive")

    user.reset_failed_attempts()
    token_pair = await _issue_token_pair(session, user)
    return _set_cookies_on_response(response, token_pair)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=CookieTokenResponse)
async def signup(
    body: SignupRequest,
    response: Response,
    session: Session,
) -> CookieTokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    session.add(user)
    await session.flush()

    org = Organization(name=f"{user.name}'s Org", slug=f"user-{user.public_id}")
    session.add(org)
    await session.flush()

    membership = UserOrganizationMembership(
        user_id=user.id, organization_id=org.id, role="org_admin"
    )
    session.add(membership)
    await session.flush()

    token_pair = await _issue_token_pair(session, user)
    return _set_cookies_on_response(response, token_pair)


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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token provided")

    token_hash = hash_token(refresh_token_value)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    old_token = result.scalar_one_or_none()

    if not old_token or not old_token.is_valid():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user_result = await session.execute(select(User).where(User.id == old_token.user_id))
    user = user_result.scalar_one()

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User account is inactive")

    old_token.revoked = True
    token_pair = await _issue_token_pair(session, user)
    return _set_cookies_on_response(response, token_pair)


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
        is_superuser=user.is_superuser,
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
        is_superuser=user.is_superuser,
        created_at=user.created_at,
    )
