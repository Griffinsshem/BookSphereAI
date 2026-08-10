from __future__ import annotations
import uuid

import pytest

from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    DuplicatePendingInviteError,
    InviteAlreadyAcceptedError,
    InviteExpiredError,
    InviteNotFoundError,
)
from booksphere.models.user import User
from booksphere.services.team.invite_service import InviteService
from tests.unit.services.fakes_team import (
    FakeInviteRepository,
    FakeMembershipRepositoryForTeam,
    FakeUserRepositoryForTeam,
)


@pytest.fixture
def invite_service(monkeypatch):
    # send_invite_email.delay() would otherwise try to reach a real
    # Celery broker (Redis) during a unit test -- monkeypatched to a
    # no-op that records calls, so we can assert an email WOULD have
    # been enqueued without actually requiring Redis for this test.
    import booksphere.services.team.invite_service as invite_module

    calls = []

    class FakeTask:
        def delay(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(invite_module, "send_invite_email", FakeTask())

    service = InviteService(
        FakeInviteRepository(), FakeMembershipRepositoryForTeam(), FakeUserRepositoryForTeam()
    )
    service._test_email_calls = calls  # attached for test inspection
    return service


class TestCreateInvite:
    def test_creates_pending_invite(self, invite_service):
        org_id = uuid.uuid4()
        inviter_id = uuid.uuid4()

        invite = invite_service.create_invite(
            organization_id=org_id,
            email="NewPerson@Example.com",
            role="staff",
            invited_by_user_id=inviter_id,
            organization_name="Test Org",
            inviter_name="Test Inviter",
            frontend_base_url="http://localhost:3000",
        )

        assert invite.status == "pending"
        assert invite.email == "newperson@example.com"  # normalized

    def test_enqueues_email_task(self, invite_service):
        invite_service.create_invite(
            organization_id=uuid.uuid4(),
            email="someone@example.com",
            role="staff",
            invited_by_user_id=uuid.uuid4(),
            organization_name="Test Org",
            inviter_name="Test Inviter",
            frontend_base_url="http://localhost:3000",
        )
        assert len(invite_service._test_email_calls) == 1
        assert invite_service._test_email_calls[0]["to_email"] == "someone@example.com"

    def test_rejects_granting_owner_role(self, invite_service):
        with pytest.raises(CannotModifyOwnerRoleError):
            invite_service.create_invite(
                organization_id=uuid.uuid4(),
                email="wouldbeowner@example.com",
                role="owner",
                invited_by_user_id=uuid.uuid4(),
                organization_name="Test Org",
                inviter_name="Test Inviter",
                frontend_base_url="http://localhost:3000",
            )

    def test_rejects_duplicate_pending_invite(self, invite_service):
        org_id = uuid.uuid4()
        kwargs = dict(
            organization_id=org_id,
            email="dup@example.com",
            role="staff",
            invited_by_user_id=uuid.uuid4(),
            organization_name="Test Org",
            inviter_name="Test Inviter",
            frontend_base_url="http://localhost:3000",
        )
        invite_service.create_invite(**kwargs)
        with pytest.raises(DuplicatePendingInviteError):
            invite_service.create_invite(**kwargs)

    def test_behaves_identically_whether_or_not_email_has_an_account(
        self, invite_service
    ):
        """SECURITY-CRITICAL: this is the email-enumeration defense.
        create_invite() must succeed identically (same return shape,
        no distinguishing error) whether the invited email belongs to
        an existing registered User or not -- an inviter must never be
        able to learn 'this person already has a BookSphere account'
        simply by trying to invite them. Note create_invite() doesn't
        even LOOK UP the User by email at all -- proving this by
        construction, not just by testing two cases and hoping they
        happen to match."""
        import inspect

        source = inspect.getsource(invite_service.create_invite)
        assert "self._users" not in source, (
            "create_invite() must never query the user repository by "
            "email -- doing so would create an email-enumeration "
            "side-channel even if the two code paths currently return "
            "the same thing."
        )


class TestGetInviteByToken:
    def test_raises_not_found_for_unknown_token(self, invite_service):
        with pytest.raises(InviteNotFoundError):
            invite_service.get_invite_by_token("nonexistent-token")

    def test_raises_expired_for_past_expiry(self, invite_service, monkeypatch):
        """Uses a known raw token by monkeypatching hash_token to the
        identity function for this test only -- lets us construct an
        invite whose token_hash we control, then look it up by that
        same known raw value, without needing create_invite() to
        (incorrectly) expose its raw token."""
        from datetime import datetime, timedelta, timezone
        import booksphere.services.team.invite_service as invite_module

        monkeypatch.setattr(invite_module, "hash_token", lambda raw: raw)

        invite = invite_service.create_invite(
            organization_id=uuid.uuid4(),
            email="expiring@example.com",
            role="staff",
            invited_by_user_id=uuid.uuid4(),
            organization_name="Test Org",
            inviter_name="Test Inviter",
            frontend_base_url="http://localhost:3000",
        )
        invite.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(InviteExpiredError):
            # With hash_token patched to identity, token_hash IS the
            # raw token we can look up with directly.
            invite_service.get_invite_by_token(invite.token_hash)

    def test_raises_already_accepted(self, invite_service, monkeypatch):
        import booksphere.services.team.invite_service as invite_module

        monkeypatch.setattr(invite_module, "hash_token", lambda raw: raw)

        invite = invite_service.create_invite(
            organization_id=uuid.uuid4(),
            email="accepted@example.com",
            role="staff",
            invited_by_user_id=uuid.uuid4(),
            organization_name="Test Org",
            inviter_name="Test Inviter",
            frontend_base_url="http://localhost:3000",
        )
        invite.status = "accepted"

        with pytest.raises(InviteAlreadyAcceptedError):
            invite_service.get_invite_by_token(invite.token_hash)
