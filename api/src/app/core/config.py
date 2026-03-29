"""Application settings."""

import os
import secrets
import sys
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_running_pytest() -> bool:
    if "pytest" in sys.modules:
        return True
    if any(key.startswith(("PYTEST_", "_PYTEST_")) for key in os.environ):
        return True
    return any("pytest" in arg for arg in sys.argv)


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class APISettings(PydanticBaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    frontend_url: str = "http://localhost:3000"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=365)


class CORSSettings(PydanticBaseModel):
    allow_origins: list[str] = ["*"]


class GoogleOAuthSettings(PydanticBaseModel):
    client_id: str | None = None
    client_secret: str | None = None
    enabled: bool = True
    redirect_uri: str | None = None


class OAuthSettings(PydanticBaseModel):
    google: GoogleOAuthSettings = Field(default_factory=GoogleOAuthSettings)
    state_ttl_seconds: int = Field(default=600, ge=60, le=3600)
    frontend_success_url: str = "http://localhost:3000/oauth/callback"
    frontend_error_url: str = "http://localhost:3000/oauth/error"


class CookieSettings(PydanticBaseModel):
    domain: str | None = None
    path: str = "/"
    secure: bool = False
    samesite: Literal["lax", "strict", "none"] = "lax"
    httponly: bool = True
    access_token_cookie_name: str = "app_access"
    refresh_token_cookie_name: str = "app_refresh"
    csrf_token_cookie_name: str = "app_csrf"


class AuthSettings(PydanticBaseModel):
    max_failed_login_attempts: int = Field(default=5, ge=1, le=20)
    lockout_base_duration_minutes: int = Field(default=1, ge=1, le=60)
    lockout_max_duration_minutes: int = Field(default=60, ge=1, le=1440)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    environment: Environment = Field(default=Environment.DEVELOPMENT)

    api: APISettings = Field(default_factory=APISettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    oauth: OAuthSettings = Field(default_factory=OAuthSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    cookie: CookieSettings = Field(default_factory=CookieSettings)

    database_url: str | None = Field(
        default="postgresql://app:app@localhost:5434/app",
    )
    redis_url: str = Field(default="redis://localhost:6381")
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=15, ge=0, le=100)
    database_echo: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    secret_key: str | None = Field(default=None)
    upload_dir: str = Field(default="./uploads")

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, data: dict[str, Any]) -> dict[str, Any]:
        if _is_running_pytest():
            data["environment"] = Environment.TEST
        return data

    @model_validator(mode="after")
    def validate_and_set_defaults(self) -> "Settings":
        if self.environment == Environment.TEST:
            self.database_pool_size = 1
            self.database_max_overflow = 0

        if self.environment in (Environment.PRODUCTION, Environment.STAGING):
            self.cookie.secure = True

        if not self.secret_key:
            if self.environment in (Environment.DEVELOPMENT, Environment.TEST):
                self.secret_key = secrets.token_urlsafe(32)
            else:
                msg = f"SECRET_KEY must be set in {self.environment.value} environment."
                raise ValueError(msg)
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_test(self) -> bool:
        return self.environment == Environment.TEST


settings = Settings()
