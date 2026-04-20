"""Project model."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import HouseholdScopedBaseModel, PublicIDMixin


class Project(HouseholdScopedBaseModel, PublicIDMixin):
    __tablename__ = "app_projects"
    _public_id_prefix = "proj_"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("app_areas.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    lead_member_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_household_members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    for_member_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_household_members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
