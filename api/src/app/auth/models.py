"""Auth domain models."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModel, MembershipBaseModel, PublicIDMixin

if TYPE_CHECKING:
    from app.auth.oauth.models import OAuthAccount


class User(BaseModel, PublicIDMixin):
    __tablename__ = "app_users"
    _public_id_prefix = "user_"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list["UserOrganizationMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def is_locked(self) -> bool:
        return self.locked_until is not None and datetime.now(UTC) < self.locked_until

    def lock_account(self, base_minutes: int, max_minutes: int) -> None:
        lockout_count = self.failed_login_attempts // 5
        duration = min(base_minutes * (2**lockout_count), max_minutes)
        self.locked_until = datetime.now(UTC) + timedelta(minutes=duration)

    def reset_failed_attempts(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None

    def increment_failed_attempts(self) -> None:
        self.failed_login_attempts += 1


class Organization(BaseModel, PublicIDMixin):
    __tablename__ = "app_organizations"
    _public_id_prefix = "org_"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    memberships: Mapped[list["UserOrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class UserOrganizationMembership(MembershipBaseModel):
    __tablename__ = "app_user_organization_memberships"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_users.id", ondelete="CASCADE"), primary_key=True
    )
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_organizations.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")

    user: Mapped["User"] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship(back_populates="memberships")


class RefreshToken(BaseModel, PublicIDMixin):
    __tablename__ = "app_refresh_tokens"
    _public_id_prefix = "rt_"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User")

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired()
