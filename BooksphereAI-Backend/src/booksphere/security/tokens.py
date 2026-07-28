"""
Opaque token generation and hashing for refresh tokens and CSRF tokens.

Uses `secrets` (not `random`) because these values must be
cryptographically unpredictable — `random` is not safe for
security-sensitive tokens.
"""
from __future__ import annotations

import hashlib
import secrets


def generate_opaque_token() -> str:
    """A URL-safe, 256-bit random token, suitable as a refresh token
    or CSRF token value."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """SHA-256 hash of a token, for storage.

    SHA-256 (not Argon2) is appropriate here because, unlike passwords,
    these tokens are already high-entropy random values, not
    low-entropy human-chosen secrets — there's no offline
    guessing-attack risk to defend against with a slow hash.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
