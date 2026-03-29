"""OAuth business logic — user lookup/creation, token generation."""

from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.jwt import create_access_token
from app.auth.models import Organization, User, UserOrganizationMembership
from app.auth.oauth.models import OAuthAccount
from app.auth.service import create_refresh_token
from app.core.config import settings


async def create_oauth_tokens(
    session: AsyncSession,
    user: User,
) -> tuple[str, str, int]:
    access_token = create_access_token(
        data={"sub": user.public_id, "type": "access"},
        expires_delta=timedelta(minutes=settings.api.access_token_expire_minutes),
    )
    refresh_token_str, _ = await create_refresh_token(session, user.id)
    return access_token, refresh_token_str, settings.api.access_token_expire_minutes * 60


async def find_or_create_user_oauth(
    session: AsyncSession,
    provider: str,
    user_info: dict[str, Any],
) -> tuple[User, OAuthAccount, bool, bool]:
    """Find or create a user from OAuth provider info.

    Returns (user, oauth_account, is_new_user, is_new_link).
    """
    email = user_info["email"].lower()
    provider_user_id = user_info["sub"]

    existing_oauth = await session.scalar(
        select(OAuthAccount)
        .options(selectinload(OAuthAccount.user))
        .where(OAuthAccount.provider == provider)
        .where(OAuthAccount.provider_user_id == provider_user_id)
    )

    if existing_oauth:
        existing_oauth.last_used_at = datetime.now(UTC)
        return existing_oauth.user, existing_oauth, False, False

    user = await session.scalar(select(User).where(func.lower(User.email) == email))

    if user:
        oauth_account = _build_oauth_account(user.id, provider, user_info)
        session.add(oauth_account)
        await session.flush()
        return user, oauth_account, False, True

    user = User(
        email=email,
        name=user_info.get("name", email.split("@")[0]),
        password_hash=None,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    oauth_account = _build_oauth_account(user.id, provider, user_info)
    session.add(oauth_account)

    org = Organization(name=f"{user.name}'s Org", slug=f"user-{user.public_id}")
    session.add(org)
    await session.flush()

    membership = UserOrganizationMembership(
        user_id=user.id, organization_id=org.id, role="org_admin"
    )
    session.add(membership)
    await session.flush()

    logger.info(
        "Created new user via OAuth: user_id={uid}, provider={p}", uid=user.id, p=provider
    )
    return user, oauth_account, True, True


def _build_oauth_account(
    user_id: int,
    provider: str,
    user_info: dict[str, Any],
) -> OAuthAccount:
    return OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_user_id=user_info["sub"],
        email=user_info["email"].lower(),
        email_verified=user_info.get("email_verified", False),
        provider_name=user_info.get("name"),
        avatar_url=user_info.get("picture"),
        last_used_at=datetime.now(UTC),
    )
