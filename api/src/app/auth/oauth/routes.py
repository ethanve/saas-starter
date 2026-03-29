"""OAuth authentication routes."""

import secrets
from typing import Any, Literal
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger

from app.auth.cookies import set_auth_cookies
from app.auth.oauth.client import get_oauth
from app.auth.oauth.redis import (
    consume_auth_code,
    create_auth_code,
    create_oauth_state,
    validate_oauth_state,
)
from app.auth.oauth.services import create_oauth_tokens, find_or_create_user_oauth
from app.auth.schemas import CookieTokenResponse
from app.core.config import settings
from app.core.database import Session

router = APIRouter(prefix="/oauth", tags=["oauth"])

OAuthProvider = Literal["google"]


def _is_provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(
            settings.oauth.google.enabled
            and settings.oauth.google.client_id
            and settings.oauth.google.client_secret
            and settings.oauth.google.redirect_uri
        )
    return False


def _redirect_error(message: str) -> RedirectResponse:
    params = {"error": message}
    return RedirectResponse(
        url=f"{settings.oauth.frontend_error_url}?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )


def _extract_user_info(token: dict[str, Any]) -> dict[str, Any] | None:
    userinfo = token.get("userinfo")
    if userinfo:
        return {
            "sub": userinfo.get("sub"),
            "email": userinfo.get("email"),
            "email_verified": userinfo.get("email_verified", False),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
        }
    return None


@router.get("/{provider}/login")
async def oauth_login(request: Request, provider: OAuthProvider) -> RedirectResponse:
    if not _is_provider_configured(provider):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"{provider.capitalize()} OAuth is not configured",
        )

    oauth = get_oauth()
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OAuth client not available")

    state = secrets.token_urlsafe(32)
    await create_oauth_state(state, provider)

    redirect_uri = settings.oauth.google.redirect_uri
    return await client.authorize_redirect(request, redirect_uri, state=state)


@router.get("/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: OAuthProvider,
    session: Session,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    if error:
        return _redirect_error(f"OAuth error: {error_description or error}")

    if not code or not state:
        return _redirect_error("Missing authorization code or state")

    state_data = await validate_oauth_state(state)
    if not state_data or state_data.get("provider") != provider:
        return _redirect_error("Invalid or expired OAuth session")

    try:
        oauth = get_oauth()
        client = oauth.create_client(provider)
        if client is None:
            return _redirect_error("OAuth client not available")
        token = await client.authorize_access_token(request)
    except OAuthError as e:
        logger.warning("OAuth token exchange failed: {err}", err=str(e))
        return _redirect_error("Failed to complete OAuth authentication")

    user_info = _extract_user_info(token)
    if not user_info or not user_info.get("email"):
        return _redirect_error("Failed to get user information from provider")

    if not user_info.get("email_verified", False):
        return _redirect_error("Email not verified by provider")

    user, _oauth_account, _is_new_user, _is_new_link = await find_or_create_user_oauth(
        session, provider, user_info
    )

    if not user.is_active:
        return _redirect_error("User account is inactive")

    if user.failed_login_attempts > 0:
        user.reset_failed_attempts()

    access_token, refresh_token_str, expires_in = await create_oauth_tokens(session, user)

    auth_code = await create_auth_code(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=expires_in,
        user_id=user.public_id,
    )

    redirect_url = f"{settings.oauth.frontend_success_url}?{urlencode({'code': auth_code})}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/exchange", response_model=CookieTokenResponse)
async def exchange_auth_code(
    body: dict,
    response: Response,
) -> CookieTokenResponse:
    code = body.get("code")
    if not code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing authorization code")

    data = await consume_auth_code(code)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired authorization code")

    csrf_token = set_auth_cookies(
        response,
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        access_max_age=data["expires_in"],
        refresh_max_age=settings.api.refresh_token_expire_days * 86400,
    )

    return CookieTokenResponse(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        token_type="bearer",
        expires_in=data["expires_in"],
        csrf_token=csrf_token,
    )
