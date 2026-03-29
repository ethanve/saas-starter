"""FastAPI application setup."""

import re
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, Response

from app import __version__
from app.api import api_router
from app.auth.oauth.client import configure_oauth
from app.core.config import settings
from app.core.errors import ErrorResponse
from app.core.exceptions import AppException
from app.core.lifespan import lifespan
from app.core.middleware import AccessLogMiddleware, RequestContextMiddleware

configure_oauth()


async def app_error_handler(request: Request, exc: AppException) -> Response:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=str(exc) or exc.message,
            details=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


async def not_found_handler(request: Request, exc: Exception) -> Response:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="NOT_FOUND",
            message="The requested resource was not found.",
            request_id=request_id,
        ).model_dump(),
    )


_DATABASE_ERROR_PATTERNS: list[tuple[str, str]] = [
    (r"duplicate key value violates unique constraint", "This item already exists."),
    (r"violates foreign key constraint", "This item is referenced by other data."),
    (r"violates not-null constraint", "A required field is missing."),
]


def _sanitize_database_error(exc: Exception) -> str:
    error_str = str(exc)
    for pattern, message in _DATABASE_ERROR_PATTERNS:
        if re.search(pattern, error_str, re.I):
            return message
    return "A database error occurred. Please try again."


async def database_error_handler(request: Request, exc: Exception) -> Response:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Database error: {error}", error=str(exc), exc_info=exc)

    if isinstance(exc, IntegrityError):
        error_str = str(exc)
        if "duplicate key" in error_str.lower():
            status_code = status.HTTP_409_CONFLICT
            error_code = "CONFLICT"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_code = "BAD_REQUEST"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "DATABASE_ERROR"

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error_code,
            message=_sanitize_database_error(exc),
            request_id=request_id,
        ).model_dump(),
    )


exception_handlers: dict[int | type[Exception], Any] = {
    404: not_found_handler,
    AppException: app_error_handler,
    IntegrityError: database_error_handler,
    OperationalError: database_error_handler,
}

app = FastAPI(
    title="SaaS Starter API",
    version=__version__,
    exception_handlers=exception_handlers,
    lifespan=lifespan,
)

app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestContextMiddleware)

assert settings.secret_key is not None
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=600,
    same_site="lax",
    https_only=settings.is_production,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
