"""
Pure availability computation -- given working hours and existing
bookings, compute open time slots. No DB access here; this module
receives already-fetched data and returns computed results, which is
what makes it unit-testable without a database at all.
"""
from __future__ import annotations
from datetime import date as date_type, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from booksphere.models.booking import Booking
from booksphere.models.working_hours import WorkingHours


def _combine_local(day: date_type, clock_time: time, tz: ZoneInfo) -> datetime:
    """Combines a date + wall-clock time AS IF IN THE GIVEN TIMEZONE,
    then returns the equivalent UTC instant -- this is what correctly
    turns "9am on this working-hours row" into the right actual moment
    in time, for any organization regardless of where it's located."""
    local_dt = datetime.combine(day, clock_time, tzinfo=tz)
    return local_dt.astimezone(timezone.utc)


def _overlaps(slot_start: datetime, slot_end: datetime, booking: Booking) -> bool:
    # Standard interval-overlap check: two ranges overlap unless one
    # ends before the other starts (in either direction).
    return slot_start < booking.end_time and booking.start_time < slot_end


def compute_available_slots(
    target_date: date_type,
    duration_minutes: int,
    working_hours: list[WorkingHours],
    existing_bookings: list[Booking],
    org_timezone: str = "UTC",
) -> list[datetime]:
    """Returns a list of available slot START times for the given date,
    as UTC datetimes (matching how Booking.start_time is always
    stored/compared) -- computed from working hours that are wall-clock
    times in the ORGANIZATION's local timezone.

    Each returned datetime represents a slot of length duration_minutes
    that fits entirely within a working-hours window and does not
    overlap any existing confirmed booking.
    """
    tz = ZoneInfo(org_timezone)
    day_of_week = target_date.weekday()
    relevant_windows = [w for w in working_hours if w.day_of_week == day_of_week]

    now = datetime.now(timezone.utc)
    slots: list[datetime] = []

    for window in relevant_windows:
        window_start = _combine_local(target_date, window.start_time, tz)
        window_end = _combine_local(target_date, window.end_time, tz)

        candidate = window_start
        step = timedelta(minutes=duration_minutes)

        while candidate + step <= window_end:
            slot_end = candidate + step

            # Skip anything already in the past -- relevant when
            # target_date is today and part of the working window has
            # already elapsed.
            if candidate < now:
                candidate += step
                continue

            has_conflict = any(
                _overlaps(candidate, slot_end, booking) for booking in existing_bookings
            )

            if not has_conflict:
                slots.append(candidate)

            candidate += step

    return slots
