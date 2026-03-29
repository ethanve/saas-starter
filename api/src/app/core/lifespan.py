"""FastAPI lifespan event handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis_client, init_redis


async def _startup() -> None:
    try:
        if settings.database_url:
            await init_db()
    except Exception:
        logger.exception("Failed to initialize database")

    try:
        await init_redis()
    except Exception:
        logger.exception("Failed to initialize Redis")


async def _shutdown() -> None:
    try:
        await close_redis_client()
    except Exception:
        logger.exception("Error closing Redis")

    try:
        if settings.database_url:
            await close_db()
    except Exception:
        logger.exception("Error closing database")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _startup()
    yield
    await _shutdown()
