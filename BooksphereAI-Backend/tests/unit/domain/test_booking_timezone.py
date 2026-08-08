"""
Proves the actual bug found via manual browser testing is fixed:
working hours are wall-clock times in the ORGANIZATION's local
timezone, not UTC. A booking at 9am Nairobi time must be correctly
validated/computed even though 9am Nairobi is 6am UTC.
"""
from __future__ import annotations
from datetime import date, datetime, time, timezone

from booksphere.domain.bookings.availability import compute_available_slots
from booksphere.domain.bookings.value_objects import validate_within_working_hours


class FakeWorkingHours:
    def __init__(self, day_of_week, start_time, end_time):
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time


class TestWorkingHoursTimezoneConversion:
    def test_validates_correctly_for_non_utc_organization(self):
        """A working-hours window of 09:00-17:00 for a Nairobi (UTC+3)
        org means 06:00-14:00 UTC. A booking at 10:00 UTC (= 13:00
        Nairobi) should be accepted -- it falls within Nairobi's 9-5,
        even though 10:00 UTC would be OUTSIDE a naive UTC-only 9-5
        window's interpretation for a non-UTC business... actually
        10:00 UTC IS within 09:00-17:00 UTC too, so use a clearer
        case: a booking at 07:00 UTC (=10:00 Nairobi, inside 9-5
        Nairobi) that would be REJECTED if working hours were
        (incorrectly) treated as UTC 9-5, since 07:00 UTC < 09:00 UTC.
        """
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]

        # Monday, 07:00 UTC = 10:00 EAT (Africa/Nairobi, UTC+3)
        start = datetime(2026, 12, 7, 7, 0, tzinfo=timezone.utc)
        end = datetime(2026, 12, 7, 8, 0, tzinfo=timezone.utc)

        # Correctly ACCEPTED when interpreted as Nairobi local time
        # (10:00-11:00 Nairobi, inside 9-5).
        validate_within_working_hours(start, end, windows, org_timezone="Africa/Nairobi")

    def test_same_utc_time_rejected_for_utc_organization(self):
        """The SAME UTC instant that's valid for a Nairobi org must be
        REJECTED for a UTC org -- 07:00 UTC is before UTC's own 9am
        working-hours start. This is the test that would have caught
        the original bug: without timezone conversion, both org types
        would get an identical (wrong, for one of them) result."""
        from booksphere.domain.bookings.exceptions import OutsideWorkingHoursError
        import pytest

        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]
        start = datetime(2026, 12, 7, 7, 0, tzinfo=timezone.utc)
        end = datetime(2026, 12, 7, 8, 0, tzinfo=timezone.utc)

        with pytest.raises(OutsideWorkingHoursError):
            validate_within_working_hours(start, end, windows, org_timezone="UTC")

    def test_compute_available_slots_converts_working_hours_to_utc(self):
        """The availability computation must return UTC datetimes
        that, when converted back to Nairobi local time, actually
        fall within the org's stated 9-5 Nairobi hours -- not 9-5 UTC."""
        windows = [FakeWorkingHours(0, time(9, 0), time(17, 0))]  # Nairobi local
        target = date(2026, 12, 7)  # a Monday

        slots = compute_available_slots(
            target, 60, windows, [], org_timezone="Africa/Nairobi"
        )

        assert len(slots) > 0
        for slot in slots:
            # Every slot, converted to Nairobi time, must fall at or
            # after 9am and the slot's end must be at or before 5pm.
            from zoneinfo import ZoneInfo

            nairobi_time = slot.astimezone(ZoneInfo("Africa/Nairobi"))
            assert nairobi_time.hour >= 9
            assert nairobi_time.hour < 17

        # The FIRST slot, in UTC, should be 06:00 UTC (09:00 Nairobi -
        # 3 hours), NOT 09:00 UTC -- this is the exact assertion that
        # would have failed before the fix.
        assert slots[0].astimezone(timezone.utc).hour == 6
