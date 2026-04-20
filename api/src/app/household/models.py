"""Household domain models."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModel, HouseholdScopedBaseModel, MembershipBaseModel, PublicIDMixin

if TYPE_CHECKING:
    from app.auth.models import User


class MemberKind(StrEnum):
    ADULT = "adult"
    KID = "kid"
    EXTERNAL = "external"


class Household(BaseModel, PublicIDMixin):
    __tablename__ = "app_households"
    _public_id_prefix = "hh_"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    memberships: Mapped[list["HouseholdMembership"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
    members: Mapped[list["HouseholdMember"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )


class HouseholdMembership(MembershipBaseModel):
    __tablename__ = "app_household_memberships"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_users.id", ondelete="CASCADE"), primary_key=True
    )
    household_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_households.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="memberships")
    household: Mapped["Household"] = relationship(back_populates="memberships")


class HouseholdMember(HouseholdScopedBaseModel, PublicIDMixin):
    __tablename__ = "app_household_members"
    _public_id_prefix = "mem_"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short: Mapped[str] = mapped_column(String(8), nullable=False)
    color: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default=MemberKind.ADULT.value)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    household: Mapped["Household"] = relationship(back_populates="members")
    user: Mapped["User | None"] = relationship("User")
