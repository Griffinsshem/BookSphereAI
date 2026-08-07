from __future__ import annotations
from datetime import date as date_type, datetime, time, timezone
from uuid import UUID

from booksphere.extensions import db
from booksphere.models.booking import Booking
from booksphere.models.resource import Resource
from booksphere.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    def lock_resource_for_booking(self, resource_id: UUID) -> Resource | None:
        """SELECT ... FOR UPDATE on the resource row itself.

        This is the row-level lock described in the feature design:
        serializes concurrent booking ATTEMPTS for the same resource,
        so the second of two simultaneous requests re-checks
        availability only after the first has actually committed --
        letting us return a clean SlotUnavailableError instead of
        relying on the exclusion constraint's raw IntegrityError as
        the only signal. Must be called within an existing
        transaction; the lock is released on commit/rollback.
        """
        return db.session.query(Resource).filter_by(id=resource_id).with_for_update().first()

    def get_confirmed_bookings_for_date(
        self, resource_id: UUID, target_date: date_type
    ) -> list[Booking]:
        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        return (
            Booking.query.filter_by(resource_id=resource_id, status="confirmed")
            .filter(Booking.start_time <= day_end, Booking.end_time >= day_start)
            .all()
        )

    def get_for_organization(self, booking_id: UUID, organization_id: UUID) -> Booking | None:
        # Same IDOR-safe pattern as ResourceRepository/ServiceRepository
        # -- filters by id AND organization_id in one query, so a
        # cross-tenant guess returns None, identical to "doesn't exist."
        return Booking.query.filter_by(id=booking_id, organization_id=organization_id).first()

    def list_for_organization(
        self,
        organization_id: UUID,
        customer_id: UUID | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        query = Booking.query.filter_by(organization_id=organization_id)
        if customer_id is not None:
            # Enforces "customers see only their own bookings" at the
            # query level -- the service layer decides WHETHER to pass
            # this filter (based on the requester's role), but once
            # decided, the query itself guarantees the restriction.
            query = query.filter_by(customer_id=customer_id)
        return query.order_by(Booking.start_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
