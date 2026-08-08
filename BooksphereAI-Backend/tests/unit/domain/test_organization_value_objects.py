from __future__ import annotations
import pytest

from booksphere.domain.organizations.exceptions import InvalidTimezoneError
from booksphere.domain.organizations.value_objects import validate_timezone


class TestValidateTimezone:
    def test_accepts_valid_iana_timezone(self):
        validate_timezone("Africa/Nairobi")  # should not raise
        validate_timezone("America/New_York")
        validate_timezone("UTC")

    def test_rejects_invalid_timezone(self):
        with pytest.raises(InvalidTimezoneError):
            validate_timezone("Not/A/Real/Timezone")

    def test_rejects_empty_string(self):
        with pytest.raises(InvalidTimezoneError):
            validate_timezone("")
