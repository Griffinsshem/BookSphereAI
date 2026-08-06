"""
Validation rules for the resources domain -- pure functions, no
framework dependency, unit-testable in isolation.
"""
from __future__ import annotations
from datetime import time

from booksphere.domain.resources.exceptions import (
    InvalidResourceTypeError,
    InvalidServiceDurationError,
    InvalidWorkingHoursError,
)

# Fixed set at the application layer (not a DB enum) -- adding a new
# resource type is a code change + deploy, not a migration. Deliberately
# conservative: only the types explicitly named in the product spec.
VALID_RESOURCE_TYPES = {
    "room",
    "equipment",
    "vehicle",
    "table",
    "meeting_space",
    "court",
    "medical_device",
    "staff",
    "service_slot",
}


def validate_resource_type(resource_type: str) -> None:
    if resource_type not in VALID_RESOURCE_TYPES:
        raise InvalidResourceTypeError(
            f"'{resource_type}' is not a valid resource type. "
            f"Must be one of: {', '.join(sorted(VALID_RESOURCE_TYPES))}"
        )


def validate_service_duration(duration_minutes: int) -> None:
    if duration_minutes <= 0:
        raise InvalidServiceDurationError("Duration must be a positive number of minutes.")
    if duration_minutes > 24 * 60:
        # A single bookable service longer than 24 hours almost
        # certainly indicates a unit-confusion bug (e.g. minutes vs.
        # days) rather than a legitimate booking -- reject rather than
        # silently accept.
        raise InvalidServiceDurationError("Duration cannot exceed 24 hours (1440 minutes).")


def validate_working_hours_window(day_of_week: int, start: time, end: time) -> None:
    if not (0 <= day_of_week <= 6):
        raise InvalidWorkingHoursError("day_of_week must be between 0 (Monday) and 6 (Sunday).")
    if start >= end:
        raise InvalidWorkingHoursError("start_time must be before end_time.")
