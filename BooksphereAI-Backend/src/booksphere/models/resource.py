"""
Resource: the generic bookable entity. Rooms, equipment, vehicles,
tables, courts, medical devices, and staff time are all modeled as
Resources with a resource_type discriminator, rather than separate
tables per type -- this is what lets the booking engine's conflict-
detection logic be written ONCE and work identically for every
bookable thing in the system.
"""
from __future__ import annotations
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Resource(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resources"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Only set when resource_type == "staff" -- links this bookable
    # resource back to the login-capable User it represents.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    working_hours: Mapped[list["WorkingHours"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
