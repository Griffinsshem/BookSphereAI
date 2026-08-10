from __future__ import annotations
import uuid

import pytest

from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    InvalidRoleError,
    MembershipNotFoundError,
)
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.services.team.membership_service import MembershipService
from tests.unit.services.fakes_team import FakeMembershipRepositoryForTeam


@pytest.fixture
def membership_service():
    return MembershipService(FakeMembershipRepositoryForTeam())


def _add_membership(service, org_id, user_id, role):
    membership = OrganizationMembership(organization_id=org_id, user_id=user_id, role=role)
    service._memberships.add(membership)
    return membership


class TestChangeRole:
    def test_promotes_staff_to_manager(self, membership_service):
        org_id, user_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, user_id, "staff")

        updated = membership_service.change_role(org_id, user_id, "manager")

        assert updated.role == "manager"

    def test_raises_when_member_not_found(self, membership_service):
        with pytest.raises(MembershipNotFoundError):
            membership_service.change_role(uuid.uuid4(), uuid.uuid4(), "manager")

    def test_cannot_change_the_owners_role(self, membership_service):
        """SECURITY-CRITICAL: an existing owner's role can never be
        changed through this endpoint -- attempting to demote the
        owner (e.g. to 'staff') must be blocked, not just attempting
        to grant owner TO someone."""
        org_id, owner_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, owner_id, "owner")

        with pytest.raises(CannotModifyOwnerRoleError):
            membership_service.change_role(org_id, owner_id, "staff")

    def test_cannot_grant_owner_role_to_a_member(self, membership_service):
        """SECURITY-CRITICAL: the reverse direction -- promoting an
        existing staff/manager member TO owner must also be blocked.
        This is the exact privilege-escalation path that motivated
        the architecture decision for this feature."""
        org_id, user_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, user_id, "manager")

        with pytest.raises(CannotModifyOwnerRoleError):
            membership_service.change_role(org_id, user_id, "owner")

    def test_rejects_invalid_role(self, membership_service):
        org_id, user_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, user_id, "staff")

        with pytest.raises(InvalidRoleError):
            membership_service.change_role(org_id, user_id, "superadmin")


class TestRemoveMember:
    def test_removes_a_non_owner_member(self, membership_service):
        org_id, user_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, user_id, "staff")

        membership_service.remove_member(org_id, user_id)

        assert membership_service._memberships.get_for_user_and_org(user_id, org_id) is None

    def test_cannot_remove_the_owner(self, membership_service):
        """SECURITY-CRITICAL: the owner can never be removed through
        this endpoint at all, regardless of how many other owners
        might theoretically exist -- this is the FIRST line of
        defense (CannotModifyOwnerRoleError), independent of and
        checked BEFORE the last-owner-count defense-in-depth check."""
        org_id, owner_id = uuid.uuid4(), uuid.uuid4()
        _add_membership(membership_service, org_id, owner_id, "owner")

        with pytest.raises(CannotModifyOwnerRoleError):
            membership_service.remove_member(org_id, owner_id)

    def test_raises_when_member_not_found(self, membership_service):
        with pytest.raises(MembershipNotFoundError):
            membership_service.remove_member(uuid.uuid4(), uuid.uuid4())


class TestListMembers:
    def test_lists_all_members_of_an_organization(self, membership_service):
        org_id = uuid.uuid4()
        _add_membership(membership_service, org_id, uuid.uuid4(), "owner")
        _add_membership(membership_service, org_id, uuid.uuid4(), "staff")
        other_org_id = uuid.uuid4()
        _add_membership(membership_service, other_org_id, uuid.uuid4(), "owner")

        members = membership_service.list_members(org_id)

        assert len(members) == 2
        assert all(m.organization_id == org_id for m in members)
