"""Authlib OAuth client configuration."""

from authlib.integrations.starlette_client import OAuth
from loguru import logger

from app.core.config import settings

GOOGLE_OPENID_CONFIG_URL = "https://accounts.google.com/.well-known/openid-configuration"

oauth = OAuth()


def configure_oauth() -> None:
    if not (settings.oauth.google.enabled and settings.oauth.google.client_id):
        logger.warning("Google OAuth not configured — missing client_id or disabled")
        return

    oauth.register(
        name="google",
        client_id=settings.oauth.google.client_id,
        client_secret=settings.oauth.google.client_secret,
        server_metadata_url=GOOGLE_OPENID_CONFIG_URL,
        client_kwargs={
            "scope": "openid email profile",
            "code_challenge_method": "S256",
        },
    )
    logger.info("Google OAuth registered successfully")


def get_oauth() -> OAuth:
    return oauth
