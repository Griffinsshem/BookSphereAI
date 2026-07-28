"""
Organization (tenant) model.

This is the root of tenant isolation: every piece of tenant-scoped
data in the system will eventually carry a foreign key back to an
Organization, directly or via a relationship chain.
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Organization(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
