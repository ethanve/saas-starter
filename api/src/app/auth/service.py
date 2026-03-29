"""Auth service — refresh tokens."""

import hashlib
from datetime import UTC, datetime, timedelta

from nanoid import generate
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.core.config import settings


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_refresh_token(
    session: AsyncSession,
    user_id: int,
    expires_days: int | None = None,
) -> tuple[str, RefreshToken]:
    if expires_days is None:
        expires_days = settings.api.refresh_token_expire_days

    token_string = generate(size=32)
    token_hash = hash_token(token_string)
    expires_at = datetime.now(UTC) + timedelta(days=expires_days)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(refresh_token)
    await session.flush()

    return token_string, refresh_token
