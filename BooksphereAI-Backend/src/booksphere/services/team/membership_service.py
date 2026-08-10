"""
MembershipService: list members, change roles, remove members.

Owner-role protection (per this feature's architecture decision):
owner can be neither granted NOR revoked through this service at
all -- not on creation (validate_assignable_role already excludes
"owner"), and not by changing/removing an EXISTING owner's
membership. Since there is currently no path in the entire codebase
that creates more than one owner (only registration sets role="owner",
exactly once, for exactly one user), this means an organization's
owner is permanently fixed until a dedicated ownership-transfer
feature exists -- a deliberate simplification, not an oversight.
"""
from __future__ import annotations
from uuid import UUID

from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    LastOwnerProtectionError,
    MembershipNotFoundError,
)
from booksphere.domain.team.value_objects import validate_assignable_role
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.security.audit_logger import log_security_event


class MembershipService:
    def __init__(self, membership_repo: MembershipRepository) -> None:
        self._memberships = membership_repo

    def list_members(self, organization_id: UUID) -> list[OrganizationMembership]:
        return self._memberships.list_for_organization_ordered(organization_id)

    def change_role(
        self, organization_id: UUID, target_user_id: UUID, new_role: str
    ) -> OrganizationMembership:
        membership = self._memberships.get_for_user_and_org(target_user_id, organization_id)
        if membership is None:
            raise MembershipNotFoundError()

        if membership.role == "owner":
            raise CannotModifyOwnerRoleError(
                "The organization owner's role cannot be changed through this endpoint."
            )

        validate_assignable_role(new_role)  # also rejects new_role == "owner"

        membership.role = new_role
        self._memberships.commit()

        log_security_event(
            "member_role_changed",
            organization_id=str(organization_id),
            target_user_id=str(target_user_id),
            new_role=new_role,
        )
        return membership

    def remove_member(self, organization_id: UUID, target_user_id: UUID) -> None:
        membership = self._memberships.get_for_user_and_org(target_user_id, organization_id)
        if membership is None:
            raise MembershipNotFoundError()

        if membership.role == "owner":
            raise CannotModifyOwnerRoleError(
                "The organization owner cannot be removed through this endpoint."
            )

        # Defense-in-depth, not currently reachable given the
        # single-owner-forever design above -- but kept as an
        # explicit, named check (rather than silently relying on the
        # CannotModifyOwnerRoleError check alone) so that IF a future
        # ownership-transfer feature ever allows multiple owners, this
        # guard is already in place rather than needing to be
        # remembered and added retroactively.
        if membership.role == "owner":
            remaining_owners = self._memberships.count_owners_for_organization(organization_id)
            if remaining_owners <= 1:
                raise LastOwnerProtectionError(
                    "Cannot remove the organization's last owner."
                )

        self._memberships.delete(membership)
        self._memberships.commit()

        log_security_event(
            "member_removed",
            organization_id=str(organization_id),
            target_user_id=str(target_user_id),
        )
