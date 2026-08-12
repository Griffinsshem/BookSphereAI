"""Domain-level exceptions for the users/auth domain.

These are raised by the service layer and translated to HTTP responses
by the centralized error handler in api/v1/errors.py — the service
layer itself knows nothing about HTTP status codes, keeping it
reusable outside a web context (e.g. from a CLI or background job).
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class EmailAlreadyRegisteredError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class OrganizationSlugTakenError(DomainError):
    pass


class InvalidRefreshTokenError(DomainError):
    pass


class VerificationTokenNotFoundError(DomainError):
    pass


class VerificationTokenExpiredError(DomainError):
    pass


class EmailAlreadyVerifiedError(DomainError):
    pass


class EmailNotVerifiedError(DomainError):
    """Raised by require_verified_email() -- distinct from the token-
    lifecycle errors above, this one gates an UNRELATED action (e.g.
    creating a booking) on the user's verification status, not on
    anything about a verification token itself."""
