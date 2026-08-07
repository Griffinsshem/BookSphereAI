"""
Pure availability computation -- given working hours and existing
bookings, compute open time slots. No DB access here; this module
receives already-fetched data and returns computed results, which is
what makes it unit-testable without a database at all.
"""
from __future__ import annotations
from datetime import date as date_type, datetime, time, timedelta, timezone

from booksphere.models.booking import Booking
from booksphere.models.working_hours import WorkingHours


def _combine(day: date_type, clock_time: time) -> datetime:
    return datetime.combine(day, clock_time, tzinfo=timezone.utc)


def _overlaps(slot_start: datetime, slot_end: datetime, booking: Booking) -> bool:
    # Standard interval-overlap check: two ranges overlap unless one
    # ends before the other starts (in either direction).
    return slot_start < booking.end_time and booking.start_time < slot_end


def compute_available_slots(
    target_date: date_type,
    duration_minutes: int,
    working_hours: list[WorkingHours],
    existing_bookings: list[Booking],
) -> list[datetime]:
    """Returns a list of available slot START times for the given date.

    Each returned datetime represents a slot of length duration_minutes
    that fits entirely within a working-hours window and does not
    overlap any existing confirmed booking.
    """
    day_of_week = target_date.weekday()
    relevant_windows = [w for w in working_hours if w.day_of_week == day_of_week]

    now = datetime.now(timezone.utc)
    slots: list[datetime] = []

    for window in relevant_windows:
        window_start = _combine(target_date, window.start_time)
        window_end = _combine(target_date, window.end_time)

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
