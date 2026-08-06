"""
WorkingHours: recurring weekly availability template for a Resource.
This is a TEMPLATE, not an actual booking or a materialized calendar --
the Booking Engine feature will use this to compute real available
time slots on specific dates, factoring in existing bookings and
one-off exceptions (holidays, etc., handled by a later feature).
"""
from __future__ import annotations
import uuid
from datetime import time as time_type

from sqlalchemy import ForeignKey, SmallInteger, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class WorkingHours(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "working_hours"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False, index=True
    )

    # 0=Monday .. 6=Sunday. No UNIQUE constraint on (resource_id,
    # day_of_week) deliberately -- a resource can have multiple
    # windows on the same day (e.g. 9-12 and 14-18 around a lunch
    # break), which is a real, common requirement.
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_type] = mapped_column(Time, nullable=False)

    resource: Mapped["Resource"] = relationship(back_populates="working_hours")
