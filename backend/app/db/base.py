"""
SQLAlchemy Base and common model utilities.

Provides the declarative base and common mixins for all models.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Automatic table name generation from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name (CamelCase to snake_case)."""
        name = cls.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in name]
        ).lstrip("_")


class TimestampMixin:
    """Mixin for automatic timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None


class AuditMixin:
    """Mixin for audit trail columns (created_by, updated_by)."""

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
