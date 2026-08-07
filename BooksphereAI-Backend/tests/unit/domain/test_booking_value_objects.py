from __future__ import annotations
from datetime import datetime, time, timedelta, timezone

import pytest

from booksphere.domain.bookings.exceptions import BookingInThePastError, OutsideWorkingHoursError
from booksphere.domain.bookings.value_objects import (
    compute_end_time,
    validate_not_in_past,
    validate_within_working_hours,
)


class FakeWorkingHours:
    """Minimal stand-in for the WorkingHours model -- only the
    attributes value_objects.py actually reads."""

    def __init__(self, day_of_week, start_time, end_time):
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time


class TestValidateNotInPast:
    def test_accepts_future_time(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        validate_not_in_past(future)  # should not raise

    def test_rejects_past_time(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(BookingInThePastError):
            validate_not_in_past(past)


class TestComputeEndTime:
    def test_adds_duration_correctly(self):
        start = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
        end = compute_end_time(start, 60)
        assert end == datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc)

    def test_handles_non_round_duration(self):
        start = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
        end = compute_end_time(start, 45)
        assert end == datetime(2026, 8, 10, 14, 45, tzinfo=timezone.utc)


class TestValidateWithinWorkingHours:
    def test_accepts_booking_fully_inside_a_window(self):
        # 2026-08-10 is a Monday (day_of_week=0)
        start = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]

        validate_within_working_hours(start, end, windows)  # should not raise

    def test_rejects_booking_outside_any_window(self):
        start = datetime(2026, 8, 10, 18, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 10, 19, 0, tzinfo=timezone.utc)
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]

        with pytest.raises(OutsideWorkingHoursError):
            validate_within_working_hours(start, end, windows)

    def test_rejects_booking_partially_outside_a_window(self):
        """A booking that STARTS inside a window but extends past its
        end must still be rejected -- fitting entirely within is
        required, not just overlapping."""
        start = datetime(2026, 8, 10, 16, 30, tzinfo=timezone.utc)
        end = datetime(2026, 8, 10, 17, 30, tzinfo=timezone.utc)
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]

        with pytest.raises(OutsideWorkingHoursError):
            validate_within_working_hours(start, end, windows)

    def test_rejects_when_no_window_exists_for_that_day(self):
        # Booking on a Tuesday (day_of_week=1) but only Monday hours exist
        start = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 11, 11, 0, tzinfo=timezone.utc)
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]

        with pytest.raises(OutsideWorkingHoursError):
            validate_within_working_hours(start, end, windows)
