"""
Tenant context resolution.

For THIS feature, no endpoint yet serves org-scoped resources (bookings,
staff, etc. don't exist yet) — so there's nothing to enforce tenant
isolation ON yet. What this module provides is the reusable MECHANISM
those future endpoints will call: given the current JWT-authenticated
user and a target organization_id, resolve whether they're a member
and what role they hold. Building this now, alongside auth, means
every future protected endpoint uses one proven helper instead of each
one reinventing (and possibly getting wrong) tenant-scoping logic.
"""
from __future__ import annotations
from uuid import UUID

from flask_jwt_extended import get_jwt_identity
from werkzeug.exceptions import Forbidden

from booksphere.repositories.membership_repository import MembershipRepository


def require_organization_role(organization_id: UUID, *allowed_roles: str) -> None:
    """Raise 403 unless the current JWT-authenticated user is a member
    of the given organization with one of the allowed roles.

    Usage in a future endpoint:
        @jwt_required()
        def some_org_scoped_endpoint(org_id):
            require_organization_role(org_id, "owner", "manager")
            ...
    """
    user_id = get_jwt_identity()
    membership = MembershipRepository().get_for_user_and_org(user_id, organization_id)

    if membership is None or membership.role not in allowed_roles:
        raise Forbidden(description="You do not have access to this organization.")


def get_membership_role(organization_id: UUID) -> str | None:
    """Returns the current JWT-authenticated user's role within the
    given organization, or None if they're not a member.

    Distinct from require_organization_role: that function only
    ANSWERS yes/no against a fixed allow-list. Some endpoints (like
    booking creation) need the actual role value to branch behavior
    -- e.g. "customers can only book for themselves; staff and above
    can book on behalf of anyone" -- which requires knowing WHICH role
    the requester has, not just whether it's in some allowed set.
    """
    user_id = get_jwt_identity()
    membership = MembershipRepository().get_for_user_and_org(user_id, organization_id)
    return membership.role if membership else None
