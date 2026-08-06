"""
Pure validation/computation logic for bookings -- no framework or DB
dependency, unit-testable in isolation.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from booksphere.domain.bookings.exceptions import (
    BookingInThePastError,
    OutsideWorkingHoursError,
)
from booksphere.models.working_hours import WorkingHours


def validate_not_in_past(start_time: datetime) -> None:
    now = datetime.now(timezone.utc)
    if start_time < now:
        raise BookingInThePastError("Cannot book a slot in the past.")


def compute_end_time(start_time: datetime, duration_minutes: int) -> datetime:
    """end_time is ALWAYS derived server-side from the service's
    duration -- never trusted from the client. A client could
    otherwise claim an arbitrarily short or long booking regardless
    of what the service actually costs in staff/resource time."""
    return start_time + timedelta(minutes=duration_minutes)


def validate_within_working_hours(
    start_time: datetime, end_time: datetime, windows: list[WorkingHours]
) -> None:
    """The booking must fit entirely inside at least one of the
    resource's working-hours windows for that day. day_of_week uses
    the same convention as WorkingHours: 0=Monday..6=Sunday, matching
    Python's datetime.weekday()."""
    day_of_week = start_time.weekday()
    start_clock = start_time.time()
    end_clock = end_time.time()

    fits_a_window = any(
        window.day_of_week == day_of_week
        and window.start_time <= start_clock
        and end_clock <= window.end_time
        for window in windows
    )

    if not fits_a_window:
        raise OutsideWorkingHoursError(
            "The requested time is outside this resource's working hours."
        )
