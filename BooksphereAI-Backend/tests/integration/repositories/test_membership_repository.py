"""
Integration tests: real Postgres, real constraints. This is what
confirms the uq_user_org UNIQUE constraint actually behaves as
designed — a unit test against a fake repository couldn't catch a
missing/wrong DB constraint.
"""
from __future__ import annotations
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from booksphere.models.organization import Organization
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.models.user import User
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.security.password_hasher import hash_password


def _make_user_and_org(db_session):
    user = User(
        email=f"test-{uuid.uuid4().hex[:12]}@example.com",
        password_hash=hash_password("correct-horse-battery-staple-1"),
        full_name="Test User",
    )
    org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:12]}")
    db_session.add(user)
    db_session.add(org)
    db_session.flush()
    return user, org


class TestMembershipRepository:
    def test_get_for_user_and_org_returns_none_when_absent(self, db_session):
        repo = MembershipRepository()
        user, org = _make_user_and_org(db_session)

        result = repo.get_for_user_and_org(user.id, org.id)

        assert result is None

    def test_get_for_user_and_org_finds_existing_membership(self, db_session):
        repo = MembershipRepository()
        user, org = _make_user_and_org(db_session)
        membership = OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="owner"
        )
        db_session.add(membership)
        db_session.flush()

        result = repo.get_for_user_and_org(user.id, org.id)

        assert result is not None
        assert result.role == "owner"

    def test_duplicate_membership_rejected_by_db_constraint(self, db_session):
        """Proves uq_user_org is a REAL database constraint, not just
        an application-level assumption we hope holds."""
        user, org = _make_user_and_org(db_session)
        db_session.add(
            OrganizationMembership(user_id=user.id, organization_id=org.id, role="owner")
        )
        db_session.flush()

        db_session.add(
            OrganizationMembership(user_id=user.id, organization_id=org.id, role="staff")
        )
        with pytest.raises(IntegrityError):
            db_session.flush()
