"""Magic-link issuance, rate-limiting, and verification."""

import hashlib
import json
import secrets
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.redis import get_redis_client
from app.email.client import send_email
from app.email.templates import magic_link_invite, magic_link_signin


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _token_key(token_hash: str) -> str:
    return f"magic:{token_hash}"


def _rate_key(email: str) -> str:
    return f"magic_rate:{email.lower()}"


@dataclass
class MagicLinkPayload:
    email: str
    name: str | None
    household_id: int | None
    member_public_id: str | None
    inviter_name: str | None


async def _enforce_rate_limit(email: str) -> None:
    redis = get_redis_client()
    key = _rate_key(email)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 3600)
    if count > settings.email.magic_link_rate_limit_per_hour:
        raise ValidationError("Too many sign-in requests. Try again later.")


async def create_magic_link(
    email: str,
    name: str | None = None,
    household_id: int | None = None,
    household_name: str | None = None,
    inviter_name: str | None = None,
    member_public_id: str | None = None,
) -> str:
    """Generate a single-use token, store it in Redis, send the email. Returns the raw token
    for dev-mode logging only — do not return it from public endpoints.
    """
    await _enforce_rate_limit(email)

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash(raw_token)
    payload = MagicLinkPayload(
        email=email.lower(),
        name=name,
        household_id=household_id,
        member_public_id=member_public_id,
        inviter_name=inviter_name,
    )

    redis = get_redis_client()
    ttl = settings.email.magic_link_ttl_minutes * 60
    await redis.set(_token_key(token_hash), json.dumps(payload.__dict__), ex=ttl)

    link = f"{settings.email.magic_link_base_url}?token={raw_token}"
    if inviter_name and household_name:
        content = magic_link_invite(link, inviter_name, household_name)
    else:
        content = magic_link_signin(link)

    await send_email(email, content)

    if settings.is_development or settings.is_test:
        logger.info("[dev] magic link for {email}: {link}", email=email, link=link)
    return raw_token


async def consume_magic_link(token: str) -> MagicLinkPayload:
    redis = get_redis_client()
    token_hash = _hash(token)
    key = _token_key(token_hash)
    # GETDEL (Redis 6.2+) reads and deletes in one atomic op, so concurrent
    # verify requests can't both see the same token.
    raw = await redis.execute_command("GETDEL", key)
    if raw is None:
        raise AuthenticationError("Invalid or expired link")
    data = json.loads(raw)
    return MagicLinkPayload(**data)


async def resolve_user_for_magic_link(
    session: AsyncSession, payload: MagicLinkPayload
) -> tuple[User, bool]:
    """Return (user, created). Creates a new user if none exists for the email.

    Two simultaneous verifies for the same new email can both pass the SELECT,
    so we catch the uniqueness violation and re-SELECT to pick up the winner.
    """
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is not None:
        return user, False

    user = User(
        email=payload.email,
        name=payload.name or payload.email.split("@", 1)[0],
        is_active=True,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one()
        return user, False
    return user, True
