from __future__ import annotations
from datetime import time

import pytest

from booksphere.domain.resources.exceptions import (
    InvalidResourceTypeError,
    InvalidServiceDurationError,
    InvalidWorkingHoursError,
)
from booksphere.domain.resources.value_objects import (
    validate_resource_type,
    validate_service_duration,
    validate_working_hours_window,
)


class TestValidateResourceType:
    def test_accepts_valid_types(self):
        for valid_type in ["room", "equipment", "staff", "vehicle"]:
            validate_resource_type(valid_type)  # should not raise

    def test_rejects_unknown_type(self):
        with pytest.raises(InvalidResourceTypeError):
            validate_resource_type("spaceship")


class TestValidateServiceDuration:
    def test_accepts_reasonable_duration(self):
        validate_service_duration(60)  # should not raise

    def test_rejects_zero_or_negative(self):
        with pytest.raises(InvalidServiceDurationError):
            validate_service_duration(0)
        with pytest.raises(InvalidServiceDurationError):
            validate_service_duration(-30)

    def test_rejects_over_24_hours(self):
        with pytest.raises(InvalidServiceDurationError):
            validate_service_duration(1441)


class TestValidateWorkingHoursWindow:
    def test_accepts_valid_window(self):
        validate_working_hours_window(0, time(9, 0), time(17, 0))  # should not raise

    def test_rejects_day_out_of_range(self):
        with pytest.raises(InvalidWorkingHoursError):
            validate_working_hours_window(7, time(9, 0), time(17, 0))
        with pytest.raises(InvalidWorkingHoursError):
            validate_working_hours_window(-1, time(9, 0), time(17, 0))

    def test_rejects_end_before_start(self):
        with pytest.raises(InvalidWorkingHoursError):
            validate_working_hours_window(0, time(17, 0), time(9, 0))

    def test_rejects_equal_start_and_end(self):
        with pytest.raises(InvalidWorkingHoursError):
            validate_working_hours_window(0, time(9, 0), time(9, 0))
