"""Area model — per-household category (kids, house, money, etc.)."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import HouseholdScopedBaseModel, PublicIDMixin


class Area(HouseholdScopedBaseModel, PublicIDMixin):
    __tablename__ = "app_areas"
    _public_id_prefix = "area_"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(32), nullable=False)
    slug: Mapped[str] = mapped_column(String(32), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
