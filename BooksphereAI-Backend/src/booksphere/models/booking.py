"""
Booking: the reservation itself.

The EXCLUSION CONSTRAINT below (ex_bookings_no_overlap) is the real
defense against double-booking -- it makes it structurally impossible
for the database to hold two CONFIRMED bookings for the same resource
with overlapping time ranges, regardless of what application code
does or doesn't check first. Row-level locking in BookingService is a
second layer on top of this, for a clean error message on conflict --
but this constraint is what actually GUARANTEES correctness, even
against a bug in that locking logic, a future second app instance, or
a direct SQL script.

Requires the btree_gist Postgres extension (enabled in this feature's
migration) -- GiST indexes natively support range-overlap operators,
but equality comparison on a plain UUID column needs btree_gist to be
usable inside a GiST-backed exclusion constraint.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Booking(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookings"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # App-layer enum, same pattern as resource_type elsewhere:
    # "confirmed" | "cancelled".
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ExcludeConstraint(
            (resource_id, "="),
            (func.tstzrange(start_time, end_time), "&&"),
            # Filtered to confirmed only -- a cancelled booking must
            # NOT continue blocking the time slot it used to occupy.
            where=(status == "confirmed"),
            name="ex_bookings_no_overlap",
            using="gist",
        ),
    )
