"""
Pure validation rules for team management -- no framework or DB
dependency.
"""
from __future__ import annotations

from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    InvalidRoleError,
)

# Roles assignable via the member-management/invite endpoints.
# "owner" is deliberately EXCLUDED here -- see
# CannotModifyOwnerRoleError. Ownership transfer is a separate,
# not-yet-built flow, not a value this endpoint can set.
ASSIGNABLE_ROLES = {"manager", "staff", "customer"}

INVITE_EXPIRY_DAYS = 7


def validate_assignable_role(role: str) -> None:
    """Validates a role for INVITES and ROLE CHANGES specifically --
    stricter than the full set of roles that can exist on a
    membership (which also includes 'owner', set only at registration
    time). Attempting to invite/promote someone to 'owner' through
    this endpoint is a distinct, explicitly named error
    (CannotModifyOwnerRoleError), not just "invalid role" -- the
    distinction matters because it signals a deliberate design
    boundary, not a typo/validation failure."""
    if role == "owner":
        raise CannotModifyOwnerRoleError(
            "Ownership cannot be granted through this endpoint. "
            "Ownership transfer is not yet supported."
        )
    if role not in ASSIGNABLE_ROLES:
        raise InvalidRoleError(
            f"'{role}' is not a valid role. Must be one of: "
            f"{', '.join(sorted(ASSIGNABLE_ROLES))}"
        )
