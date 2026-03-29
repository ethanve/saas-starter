"""Cookie helpers for httpOnly auth token management."""

import secrets

from fastapi import Request
from fastapi.responses import Response

from app.core.config import settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int,
    refresh_max_age: int,
) -> str:
    cookie = settings.cookie

    response.set_cookie(
        key=cookie.access_token_cookie_name,
        value=access_token,
        max_age=access_max_age,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=True,
        samesite=cookie.samesite,
    )

    response.set_cookie(
        key=cookie.refresh_token_cookie_name,
        value=refresh_token,
        max_age=refresh_max_age,
        path="/api/v1/auth",
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=True,
        samesite=cookie.samesite,
    )

    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=cookie.csrf_token_cookie_name,
        value=csrf_token,
        max_age=access_max_age,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=False,
        samesite=cookie.samesite,
    )

    return csrf_token


def clear_auth_cookies(response: Response) -> None:
    cookie = settings.cookie
    response.delete_cookie(
        key=cookie.access_token_cookie_name, path=cookie.path, domain=cookie.domain
    )
    response.delete_cookie(
        key=cookie.refresh_token_cookie_name, path="/api/v1/auth", domain=cookie.domain
    )
    response.delete_cookie(
        key=cookie.csrf_token_cookie_name, path=cookie.path, domain=cookie.domain
    )


def get_access_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.cookie.access_token_cookie_name)


def get_refresh_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.cookie.refresh_token_cookie_name)
