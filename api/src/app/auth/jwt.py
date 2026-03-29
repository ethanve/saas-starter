"""JWT token creation and verification."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from app.core.config import settings

ALGORITHM = "HS256"
JWT_AUDIENCE = "app-api"
JWT_ISSUER = "app"


class TokenData(BaseModel):
    sub: str
    type: str
    exp: datetime
    iat: datetime


def _get_secret_key() -> str:
    if not settings.secret_key:
        msg = "SECRET_KEY must be set"
        raise ValueError(msg)
    return settings.secret_key


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.api.access_token_expire_minutes))
    to_encode = {
        **data,
        "exp": expire,
        "iat": now,
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
    }
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={
                "require": ["exp", "iat", "sub", "aud", "iss"],
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
        return TokenData(
            sub=payload["sub"],
            type=payload.get("type", "access"),
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
        )
    except InvalidTokenError as e:
        msg = f"Invalid token: {e}"
        raise ValueError(msg) from e
