"""
Pure validation/computation logic for bookings -- no framework or DB
dependency, unit-testable in isolation.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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
    start_time: datetime,
    end_time: datetime,
    windows: list[WorkingHours],
    org_timezone: str = "UTC",
) -> None:
    """The booking must fit entirely inside at least one of the
    resource's working-hours windows for that day. day_of_week uses
    the same convention as WorkingHours: 0=Monday..6=Sunday, matching
    Python's datetime.weekday().

    WorkingHours.start_time/end_time are stored as wall-clock times in
    the ORGANIZATION's local timezone (e.g. "9am" means 9am Nairobi
    time for a Nairobi business), while start_time/end_time here are
    UTC-aware datetimes (how bookings are always stored). We must
    convert to the org's local time before comparing, or a business
    outside UTC would have every booking incorrectly rejected/accepted
    against the wrong wall-clock hours."""
    tz = ZoneInfo(org_timezone)
    local_start = start_time.astimezone(tz)
    local_end = end_time.astimezone(tz)

    day_of_week = local_start.weekday()
    start_clock = local_start.time()
    end_clock = local_end.time()

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
