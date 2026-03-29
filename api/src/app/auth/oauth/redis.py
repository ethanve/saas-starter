"""OAuth token management via Redis."""

import json
import secrets
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.core.config import settings
from app.core.redis import get_redis_client

AUTH_CODE_TTL_SECONDS = 60


async def create_oauth_state(state: str, provider: str) -> None:
    key = f"oauth:state:{state}"
    data = {"provider": provider, "created_at": datetime.now(UTC).isoformat()}
    client = get_redis_client()
    await client.setex(key, settings.oauth.state_ttl_seconds, json.dumps(data))


async def validate_oauth_state(state: str) -> dict[str, Any] | None:
    key = f"oauth:state:{state}"
    client = get_redis_client()
    try:
        data_str = await client.getdel(key)
    except Exception:
        logger.exception("Failed to retrieve OAuth state from Redis")
        return None
    if not data_str:
        return None
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        return None


async def create_auth_code(
    access_token: str,
    refresh_token: str,
    expires_in: int,
    user_id: str,
) -> str:
    code = secrets.token_urlsafe(32)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    key = f"oauth:authcode:{code}"
    client = get_redis_client()
    await client.setex(key, AUTH_CODE_TTL_SECONDS, json.dumps(data))
    return code


async def consume_auth_code(code: str) -> dict[str, Any] | None:
    key = f"oauth:authcode:{code}"
    client = get_redis_client()
    try:
        data_str = await client.getdel(key)
    except Exception:
        logger.exception("Failed to consume auth code from Redis")
        return None
    if not data_str:
        return None
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        return None
