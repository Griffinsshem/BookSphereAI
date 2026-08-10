"""
Integration test: real Postgres, real constraints. Locks in, at the
automated-suite level, the exact partial-unique-index behavior we
already verified manually via raw SQL when building the migration --
a duplicate PENDING invite to the same (org, email) is rejected, but
a duplicate to an email whose prior invite is no longer pending is
allowed.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from booksphere.models.organization import Organization
from booksphere.models.organization_invite import OrganizationInvite
from booksphere.models.user import User
from booksphere.repositories.invite_repository import InviteRepository
from booksphere.security.password_hasher import hash_password


def _make_org_and_inviter(db_session):
    org = Organization(name="Invite Test Org", slug=f"invite-test-{uuid.uuid4().hex[:12]}")
    inviter = User(
        email=f"inviter-{uuid.uuid4().hex[:12]}@example.com",
        password_hash=hash_password("correct-horse-battery-staple-1"),
        full_name="Inviter",
    )
    db_session.add(org)
    db_session.add(inviter)
    db_session.flush()
    return org, inviter


def _make_invite(org, inviter, email, token_hash, status="pending"):
    return OrganizationInvite(
        organization_id=org.id,
        email=email,
        role="staff",
        invited_by_user_id=inviter.id,
        token_hash=token_hash,
        status=status,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


class TestInviteRepositoryConstraint:
    def test_duplicate_pending_invite_rejected(self, db_session):
        org, inviter = _make_org_and_inviter(db_session)
        db_session.add(_make_invite(org, inviter, "dup@example.com", "hash-a"))
        db_session.flush()

        db_session.add(_make_invite(org, inviter, "dup@example.com", "hash-b"))
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_new_pending_invite_allowed_after_prior_one_revoked(self, db_session):
        org, inviter = _make_org_and_inviter(db_session)
        first = _make_invite(org, inviter, "revoked-then-new@example.com", "hash-c")
        db_session.add(first)
        db_session.flush()

        first.status = "revoked"
        db_session.flush()

        second = _make_invite(
            org, inviter, "revoked-then-new@example.com", "hash-d"
        )
        db_session.add(second)
        db_session.flush()  # should NOT raise

        assert second.id is not None

    def test_get_pending_for_org_and_email_ignores_non_pending(self, db_session):
        org, inviter = _make_org_and_inviter(db_session)
        accepted = _make_invite(
            org, inviter, "already-accepted@example.com", "hash-e", status="accepted"
        )
        db_session.add(accepted)
        db_session.flush()

        repo = InviteRepository()
        result = repo.get_pending_for_org_and_email(org.id, "already-accepted@example.com")

        assert result is None
