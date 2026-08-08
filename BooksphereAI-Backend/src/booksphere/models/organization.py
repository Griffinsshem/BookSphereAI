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

    # IANA timezone name (e.g. "Africa/Nairobi", "America/New_York").
    # Working hours are stored as plain wall-clock times (no tz) --
    # this field is what lets us correctly interpret "9am" as 9am IN
    # THIS ORGANIZATION'S LOCAL TIME, then convert to/from UTC for
    # actual booking storage and comparison. Defaults to UTC so
    # existing data / a business that never sets it still behaves
    # correctly, just without local-time convenience.
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC", server_default="UTC")

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
