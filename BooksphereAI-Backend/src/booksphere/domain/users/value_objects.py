"""
Value objects and validation rules for the users domain.

Password strength policy lives here — a pure function with no
framework dependency — rather than in the marshmallow schema, so it
can be unit-tested in isolation and reused anywhere (e.g. a future
"change password" feature) without re-deriving the rule.
"""
from __future__ import annotations

import re

_MIN_PASSWORD_LENGTH = 12


def is_password_strong_enough(password: str) -> bool:
    """Minimum bar: 12+ characters, at least one letter and one digit.

    12 characters (not the older "8 char + special char" advice) is
    aligned with current NIST guidance, which prioritizes length over
    forced character-class complexity — long passphrases are both more
    secure and more usable than "P@ssw0rd1" patterns.
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        return False
    has_letter = bool(re.search(r"[A-Za-z]", password))
    has_digit = bool(re.search(r"\d", password))
    return has_letter and has_digit


def slugify(name: str) -> str:
    """Convert an organization name into a URL-safe slug.

    e.g. "Acme Hotel & Spa" -> "acme-hotel-spa"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")
