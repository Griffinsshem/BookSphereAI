"""
BookingService: the transaction that actually creates a booking.

This is where every defense we've built comes together:
  1. Confirm the resource actually fulfills the requested service
     (service_resources link) -- prevents booking a massage room for
     a haircut.
  2. Compute end_time server-side from service.duration_minutes --
     never trust a client-supplied end_time.
  3. Reject bookings in the past.
  4. Lock the resource row (SELECT ... FOR UPDATE) -- serializes
     concurrent booking attempts for this resource within our own
     transaction.
  5. Re-check availability (working hours + no overlapping confirmed
     booking) AFTER acquiring the lock -- this is what makes the
     check race-free: no other transaction can commit a competing
     booking for this resource while we hold the lock.
  6. Insert the booking. Even if every check above somehow passed
     incorrectly, the ex_bookings_no_overlap EXCLUSION CONSTRAINT is
     the unconditional backstop -- verified directly against Postgres
     in the previous commit.
"""
from __future__ import annotations
from datetime import date as date_type, datetime, timezone
from uuid import UUID

from booksphere.domain.bookings.availability import compute_available_slots
from booksphere.domain.bookings.exceptions import (
    BookingAlreadyCancelledError,
    BookingInThePastError,
    BookingNotFoundError,
    OutsideWorkingHoursError,
    ResourceNotLinkedToServiceError,
    SlotUnavailableError,
)
from booksphere.domain.bookings.value_objects import (
    compute_end_time,
    validate_not_in_past,
    validate_within_working_hours,
)
from booksphere.domain.resources.exceptions import ResourceNotFoundError, ServiceNotFoundError
from booksphere.extensions import db
from booksphere.models.booking import Booking
from booksphere.repositories.booking_repository import BookingRepository
from booksphere.repositories.organization_repository import OrganizationRepository
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.service_repository import ServiceRepository
from booksphere.repositories.service_resource_repository import ServiceResourceRepository
from booksphere.repositories.working_hours_repository import WorkingHoursRepository


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        resource_repo: ResourceRepository,
        service_repo: ServiceRepository,
        service_resource_repo: ServiceResourceRepository,
        working_hours_repo: WorkingHoursRepository,
        organization_repo: OrganizationRepository,
    ) -> None:
        self._bookings = booking_repo
        self._resources = resource_repo
        self._services = service_repo
        self._service_resources = service_resource_repo
        self._working_hours = working_hours_repo
        self._organizations = organization_repo

    def _get_org_timezone(self, organization_id: UUID) -> str:
        org = self._organizations.get_by_id(organization_id)
        return org.timezone if org else "UTC"

    def get_availability(
        self,
        organization_id: UUID,
        resource_id: UUID,
        service_id: UUID,
        target_date: date_type,
    ) -> list[datetime]:
        resource = self._resources.get_for_organization(resource_id, organization_id)
        if resource is None:
            raise ResourceNotFoundError()

        service = self._services.get_for_organization(service_id, organization_id)
        if service is None:
            raise ServiceNotFoundError()

        windows = self._working_hours.list_for_resource(resource_id)
        existing_bookings = self._bookings.get_confirmed_bookings_for_date(
            resource_id, target_date
        )
        org_timezone = self._get_org_timezone(organization_id)

        return compute_available_slots(
            target_date=target_date,
            duration_minutes=service.duration_minutes,
            working_hours=windows,
            existing_bookings=existing_bookings,
            org_timezone=org_timezone,
        )

    def create_booking(
        self,
        organization_id: UUID,
        resource_id: UUID,
        service_id: UUID,
        customer_id: UUID,
        start_time: datetime,
        notes: str | None = None,
    ) -> Booking:
        service = self._services.get_for_organization(service_id, organization_id)
        if service is None:
            raise ServiceNotFoundError()

        if not self._service_resources.link_exists(service_id, resource_id):
            raise ResourceNotLinkedToServiceError(
                "This resource does not offer the requested service."
            )

        validate_not_in_past(start_time)
        end_time = compute_end_time(start_time, service.duration_minutes)

        # --- Everything from here runs under the resource row lock ---
        # SELECT ... FOR UPDATE blocks if another transaction is
        # concurrently booking the SAME resource, until that
        # transaction commits or rolls back. This is what makes the
        # availability re-check below race-free.
        resource = self._bookings.lock_resource_for_booking(resource_id)
        if resource is None or resource.organization_id != organization_id:
            raise ResourceNotFoundError()

        windows = self._working_hours.list_for_resource(resource_id)
        org_timezone = self._get_org_timezone(organization_id)
        validate_within_working_hours(start_time, end_time, windows, org_timezone)

        existing_bookings = self._bookings.get_confirmed_bookings_for_date(
            resource_id, start_time.date()
        )
        has_conflict = any(
            start_time < b.end_time and b.start_time < end_time for b in existing_bookings
        )
        if has_conflict:
            raise SlotUnavailableError("This time slot was just taken. Please choose another.")

        booking = Booking(
            organization_id=organization_id,
            resource_id=resource_id,
            service_id=service_id,
            customer_id=customer_id,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            notes=notes,
        )
        self._bookings.add(booking)
        # commit() here both releases the row lock (transaction ends)
        # AND is the point where the exclusion constraint gets its
        # final, unconditional say -- if our application-level checks
        # above somehow missed something, this is the backstop.
        self._bookings.commit()
        return booking

    def get_booking(self, booking_id: UUID, organization_id: UUID) -> Booking:
        booking = self._bookings.get_for_organization(booking_id, organization_id)
        if booking is None:
            raise BookingNotFoundError()
        return booking

    def cancel_booking(self, booking_id: UUID, organization_id: UUID) -> Booking:
        booking = self.get_booking(booking_id, organization_id)
        if booking.status == "cancelled":
            raise BookingAlreadyCancelledError()

        booking.status = "cancelled"
        booking.cancelled_at = datetime.now(timezone.utc)
        self._bookings.commit()
        return booking
