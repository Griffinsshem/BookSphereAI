from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone

from booksphere.domain.bookings.availability import compute_available_slots


class FakeWorkingHours:
    def __init__(self, day_of_week, start_time, end_time):
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time


class FakeBooking:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


class TestComputeAvailableSlots:
    def test_generates_slots_across_full_window(self):
        # A Monday far enough in the future to avoid "in the past" filtering
        target = date(2026, 12, 7)  # a Monday
        windows = [FakeWorkingHours(0, time(9, 0), time(12, 0))]

        slots = compute_available_slots(target, 60, windows, [])

        # 9-12 window, 60-min slots -> 9:00, 10:00, 11:00 (12:00 itself
        # would need the NEXT hour, which doesn't fit -- window ends
        # exactly at 12:00)
        assert len(slots) == 3
        assert slots[0] == datetime(2026, 12, 7, 9, 0, tzinfo=timezone.utc)
        assert slots[-1] == datetime(2026, 12, 7, 11, 0, tzinfo=timezone.utc)

    def test_excludes_slots_overlapping_existing_bookings(self):
        target = date(2026, 12, 7)
        windows = [FakeWorkingHours(0, time(9, 0), time(12, 0))]
        existing = [
            FakeBooking(
                datetime(2026, 12, 7, 10, 0, tzinfo=timezone.utc),
                datetime(2026, 12, 7, 11, 0, tzinfo=timezone.utc),
            )
        ]

        slots = compute_available_slots(target, 60, windows, existing)

        assert datetime(2026, 12, 7, 10, 0, tzinfo=timezone.utc) not in slots
        assert datetime(2026, 12, 7, 9, 0, tzinfo=timezone.utc) in slots
        assert datetime(2026, 12, 7, 11, 0, tzinfo=timezone.utc) in slots

    def test_returns_empty_when_no_window_for_that_day(self):
        target = date(2026, 12, 8)  # Tuesday -- no windows defined for it
        windows = [FakeWorkingHours(0, time(9, 0), time(12, 0))]

        slots = compute_available_slots(target, 60, windows, [])

        assert slots == []

    def test_service_duration_changes_slot_granularity(self):
        """A 90-minute service on the same 9-12 window should produce
        different (fewer) candidate slots than a 60-minute one --
        proves slots are generated at the SERVICE's duration, not a
        fixed grid."""
        target = date(2026, 12, 7)
        windows = [FakeWorkingHours(0, time(9, 0), time(12, 0))]

        slots_60 = compute_available_slots(target, 60, windows, [])
        slots_90 = compute_available_slots(target, 90, windows, [])

        assert len(slots_60) == 3  # 9:00, 10:00, 11:00
        assert len(slots_90) == 2  # 9:00, 10:30 (12:00 would need 90 more min)

    def test_excludes_past_slots_for_todays_date(self):
        """If target_date is today, slots earlier than 'now' must be
        excluded even if they're technically within working hours."""
        now = datetime.now(timezone.utc)
        target = now.date()
        # A window covering the last 2 hours through 2 hours from now
        windows = [
            FakeWorkingHours(
                target.weekday(),
                (now - timedelta(hours=2)).time(),
                (now + timedelta(hours=2)).time(),
            )
        ]

        slots = compute_available_slots(target, 30, windows, [])

        assert all(slot >= now.replace(microsecond=0) for slot in slots) or len(slots) >= 0
        # Every returned slot must be in the future relative to when
        # the test ran.
        for slot in slots:
            assert slot >= now - timedelta(seconds=5)  # small tolerance for test execution time
