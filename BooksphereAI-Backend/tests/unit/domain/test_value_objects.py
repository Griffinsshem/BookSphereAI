from __future__ import annotations

from booksphere.domain.users.value_objects import (
    is_password_strong_enough,
    slugify,
)


class TestPasswordStrength:
    def test_rejects_short_password(self):
        assert is_password_strong_enough("Short1") is False

    def test_rejects_letters_only(self):
        assert is_password_strong_enough("onlylettersnodigits") is False

    def test_rejects_digits_only(self):
        assert is_password_strong_enough("123456789012") is False

    def test_accepts_long_mixed_password(self):
        assert is_password_strong_enough("correct-horse-battery-1") is True


class TestSlugify:
    def test_lowercases_and_hyphenates(self):
        assert slugify("Acme Hotel & Spa") == "acme-hotel-spa"

    def test_strips_leading_trailing_hyphens(self):
        assert slugify("  !!! Weird Name !!!  ") == "weird-name"
