"""
Concurrency test: proves the double-booking defense actually holds
under REAL simultaneous load, not just sequential calls.

Uses a thread pool to fire two booking requests for the identical
resource + time slot at (as close to) the same moment as possible.
Exactly one must succeed; the other must fail with SlotUnavailableError
(the clean domain error from our row-lock logic) -- NOT an unhandled
IntegrityError, which would mean the lock isn't doing its job of
converting the exclusion constraint's raw failure into a proper
response.

Each thread needs its OWN database session -- SQLAlchemy sessions are
not thread-safe to share. We create a fresh app context and a fresh
BookingService (backed by a fresh session-scoped connection) per
thread, which also more realistically mirrors how two separate HTTP
requests would actually be handled (each with its own DB connection
from the pool).
"""
from __future__ import annotations
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone

import pytest

from booksphere.domain.bookings.exceptions import SlotUnavailableError
from booksphere.extensions import db
from booksphere.models.organization import Organization
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.models.resource import Resource
from booksphere.models.service import Service
from booksphere.models.service_resource import ServiceResource
from booksphere.models.user import User
from booksphere.models.working_hours import WorkingHours
from booksphere.repositories.booking_repository import BookingRepository
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.service_repository import ServiceRepository
from booksphere.repositories.service_resource_repository import ServiceResourceRepository
from booksphere.repositories.working_hours_repository import WorkingHoursRepository
from booksphere.security.password_hasher import hash_password
from booksphere.services.bookings.booking_service import BookingService


@pytest.fixture
def booking_setup(db_session):
    """Creates an org, a resource with working hours COVERING EVERY
    DAY (day_of_week 0-6) -- this test is about CONCURRENCY, not
    working-hours logic (already covered separately in
    test_booking_value_objects.py), so we deliberately avoid any
    dependency on which day of the week "tomorrow" happens to be when
    the test runs.

    Committed for real (not just flushed), since the concurrent
    threads below need this data visible from THEIR OWN separate
    connections, not just the fixture's uncommitted session state.
    Uses a uuid-based unique slug/email each call, since a real commit
    is NOT rolled back by db_session's usual per-test cleanup -- a
    hardcoded slug would collide across multiple tests in this file.
    """
    unique = uuid.uuid4().hex[:12]

    org = Organization(name="Concurrency Test Org", slug=f"concurrency-test-org-{unique}")
    db_session.add(org)
    db_session.flush()

    resource = Resource(organization_id=org.id, resource_type="room", name="Test Room")
    db_session.add(resource)
    db_session.flush()

    for day in range(7):
        db_session.add(
            WorkingHours(
                resource_id=resource.id,
                day_of_week=day,
                start_time=time(0, 0),
                end_time=time(23, 59),
            )
        )

    service = Service(
        organization_id=org.id, name="Test Service", duration_minutes=60, price_cents=5000
    )
    db_session.add(service)
    db_session.flush()

    db_session.add(ServiceResource(service_id=service.id, resource_id=resource.id))

    customer = User(
        email=f"concurrency-{unique}@example.com",
        password_hash=hash_password("correct-horse-battery-staple-1"),
        full_name="Concurrency Test Customer",
    )
    db_session.add(customer)
    db_session.flush()

    db_session.add(
        OrganizationMembership(user_id=customer.id, organization_id=org.id, role="customer")
    )
    db_session.commit()

    return {
        "organization_id": org.id,
        "resource_id": resource.id,
        "service_id": service.id,
        "customer_id": customer.id,
    }


def _attempt_booking(app, organization_id, resource_id, service_id, customer_id, start_time):
    """Runs in its own thread. Creates a fresh app context (and
    therefore a fresh DB session, per Flask-SQLAlchemy's scoped
    session model) so this thread's transaction is genuinely
    independent of the main test thread's.

    Returns "success", "slot_unavailable", or the exception itself
    for any unexpected failure -- lets the test assert on the exact
    outcome distribution rather than just "something happened."
    """
    with app.app_context():
        service = BookingService(
            BookingRepository(),
            ResourceRepository(),
            ServiceRepository(),
            ServiceResourceRepository(),
            WorkingHoursRepository(),
        )
        try:
            service.create_booking(
                organization_id=organization_id,
                resource_id=resource_id,
                service_id=service_id,
                customer_id=customer_id,
                start_time=start_time,
            )
            return "success"
        except SlotUnavailableError:
            return "slot_unavailable"
        except Exception as exc:  # noqa: BLE001
            return exc
        finally:
            db.session.remove()


class TestBookingConcurrency:
    def test_two_simultaneous_bookings_for_same_slot_only_one_succeeds(
        self, app, booking_setup
    ):
        start_time = datetime.now(timezone.utc) + timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(
                _attempt_booking,
                app,
                booking_setup["organization_id"],
                booking_setup["resource_id"],
                booking_setup["service_id"],
                booking_setup["customer_id"],
                start_time,
            )
            future_b = executor.submit(
                _attempt_booking,
                app,
                booking_setup["organization_id"],
                booking_setup["resource_id"],
                booking_setup["service_id"],
                booking_setup["customer_id"],
                start_time,
            )

            result_a = future_a.result(timeout=10)
            result_b = future_b.result(timeout=10)

        results = [result_a, result_b]

        # Neither thread should have hit an unexpected exception --
        # only "success" or the clean "slot_unavailable" domain error
        # are acceptable outcomes. Anything else (e.g. a raw
        # IntegrityError leaking through) means our row-lock logic
        # failed to convert the constraint violation into a proper
        # domain error.
        for result in results:
            assert result in ("success", "slot_unavailable"), (
                f"Unexpected outcome: {result!r} -- the lock should have "
                f"converted any conflict into a clean SlotUnavailableError, "
                f"never let a different exception through."
            )

        assert results.count("success") == 1, (
            f"Expected exactly one booking to succeed under concurrent "
            f"load, got: {results}"
        )
        assert results.count("slot_unavailable") == 1

    def test_two_bookings_for_different_slots_both_succeed(self, app, booking_setup):
        """Sanity check in the other direction: concurrent bookings
        for the SAME resource but DIFFERENT (non-overlapping) times
        must both succeed -- the lock serializes access, it doesn't
        block legitimate simultaneous bookings that don't conflict."""
        base = datetime.now(timezone.utc) + timedelta(days=1)
        base = base.replace(hour=10, minute=0, second=0, microsecond=0)
        slot_a = base
        slot_b = base + timedelta(hours=2)  # well clear of the 60-min service

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(
                _attempt_booking,
                app,
                booking_setup["organization_id"],
                booking_setup["resource_id"],
                booking_setup["service_id"],
                booking_setup["customer_id"],
                slot_a,
            )
            future_b = executor.submit(
                _attempt_booking,
                app,
                booking_setup["organization_id"],
                booking_setup["resource_id"],
                booking_setup["service_id"],
                booking_setup["customer_id"],
                slot_b,
            )

            result_a = future_a.result(timeout=10)
            result_b = future_b.result(timeout=10)

        assert result_a == "success"
        assert result_b == "success"
