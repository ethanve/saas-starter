"""Auth domain models — User and refresh token only. Households live in app.household.models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModel, PublicIDMixin

if TYPE_CHECKING:
    from app.household.models import HouseholdMembership


class User(BaseModel, PublicIDMixin):
    __tablename__ = "app_users"
    _public_id_prefix = "user_"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships: Mapped[list["HouseholdMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


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
