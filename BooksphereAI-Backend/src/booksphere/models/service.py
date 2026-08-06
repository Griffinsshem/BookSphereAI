"""
Service: the bookable offering a customer actually books (e.g. "60-
Minute Massage"). Distinct from Resource -- a Service is WHAT gets
booked; a Resource is the physical/staff capacity that fulfills it.
"""
from __future__ import annotations
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Service(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "services"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Integer cents, never a float -- avoids floating-point rounding
    # errors in money arithmetic. Full multi-currency/tax/discount
    # handling is deferred to the Payments feature; this is just
    # enough to display a price and, later, hand off to that feature.
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    resource_links: Mapped[list["ServiceResource"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
