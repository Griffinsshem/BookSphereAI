"""Domain exceptions for team/invite management."""
from __future__ import annotations
from booksphere.domain.users.exceptions import DomainError


class InviteNotFoundError(DomainError):
    pass


class InviteExpiredError(DomainError):
    pass


class InviteAlreadyAcceptedError(DomainError):
    pass


class DuplicatePendingInviteError(DomainError):
    pass


class InvalidRoleError(DomainError):
    pass


class CannotModifyOwnerRoleError(DomainError):
    """Raised when a request attempts to grant or revoke the 'owner'
    role through the member-management endpoint. Ownership transfer
    is deliberately a separate, not-yet-built flow -- see the
    architecture decision in this feature's analysis."""


class LastOwnerProtectionError(DomainError):
    """Raised when an action would leave the organization with zero
    owners (removing or demoting the only owner)."""


class MembershipNotFoundError(DomainError):
    pass
