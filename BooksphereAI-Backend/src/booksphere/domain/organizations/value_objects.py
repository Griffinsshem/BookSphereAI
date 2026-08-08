from __future__ import annotations
from zoneinfo import ZoneInfo, available_timezones

from booksphere.domain.organizations.exceptions import InvalidTimezoneError


def validate_timezone(tz_name: str) -> None:
    """Confirms tz_name is a real IANA timezone (e.g. 'Africa/Nairobi'),
    not just any string. Rejects garbage input before it ever reaches
    the database, where it would silently break every availability
    calculation for that organization."""
    if tz_name not in available_timezones():
        raise InvalidTimezoneError(
            f"'{tz_name}' is not a recognized timezone (expected an IANA "
            f"name like 'Africa/Nairobi' or 'America/New_York')."
        )


def get_zoneinfo(tz_name: str) -> ZoneInfo:
    return ZoneInfo(tz_name)
