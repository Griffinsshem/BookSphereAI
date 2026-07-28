"""
Password hashing via Argon2id.

A thin wrapper around argon2-cffi rather than calling it directly
throughout the codebase — if we ever need to tune parameters (memory
cost, iterations) or migrate algorithms, there's exactly one place to
change, not every call site.
"""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password. Never store the input anywhere."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Returns False on mismatch rather than raising — callers (the auth
    service) should not need to catch argon2-specific exceptions.
    """
    try:
        _hasher.verify(password_hash, plain_password)
        return True
    except VerifyMismatchError:
        return False
