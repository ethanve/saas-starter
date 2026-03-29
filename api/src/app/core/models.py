"""Base mixins for database models."""

from datetime import datetime

from nanoid import generate
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base


class TimestampMixin:
    created_at: "Mapped[datetime]" = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: "Mapped[datetime]" = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PublicIDMixin:
    @declared_attr
    def public_id(cls) -> "Mapped[str]":
        return mapped_column(String(32), nullable=False, unique=True, index=True)

    @classmethod
    def generate_public_id(cls) -> str:
        prefix = cls._public_id_prefix
        nanoid_part = generate(size=16)
        return f"{prefix}{nanoid_part}"

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_public_id_prefix"):
            msg = f"{cls.__name__} must define _public_id_prefix class attribute"
            raise TypeError(msg)


class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    id: "Mapped[int]" = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)


class MembershipBaseModel(Base, TimestampMixin):
    __abstract__ = True


class OrganizationScopedBaseModel(BaseModel):
    __abstract__ = True

    organization_id: "Mapped[int]" = mapped_column(
        BigInteger,
        ForeignKey("app_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


@listens_for(Base, "before_insert", propagate=True)
def generate_public_id_before_insert(_mapper: object, _connection: object, target: object) -> None:
    if (
        hasattr(target, "public_id")
        and hasattr(target, "_public_id_prefix")
        and not getattr(target, "public_id", None)
    ):
        target.public_id = target.generate_public_id()
