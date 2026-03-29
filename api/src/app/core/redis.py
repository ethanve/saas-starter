"""Redis client singleton."""

import redis.asyncio as redis
from loguru import logger

from app.core.config import settings

_state: dict[str, redis.Redis | None] = {"client": None}


async def init_redis() -> None:
    conn = redis.from_url(settings.redis_url, decode_responses=True)
    response = conn.ping()
    if not isinstance(response, bool):
        await response
    _state["client"] = conn
    logger.info("Redis client initialized successfully")


def get_redis_client() -> redis.Redis:
    client = _state["client"]
    if client is None:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        _state["client"] = client
    return client


async def close_redis_client() -> None:
    client = _state["client"]
    if client is not None:
        await client.aclose()
        _state["client"] = None


def reset_redis_client(client: redis.Redis | None = None) -> None:
    _state["client"] = client
