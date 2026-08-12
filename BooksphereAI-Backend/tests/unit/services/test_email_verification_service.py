from __future__ import annotations
import uuid

import pytest

from booksphere.domain.users.exceptions import (
    EmailAlreadyVerifiedError,
    VerificationTokenExpiredError,
    VerificationTokenNotFoundError,
)
from booksphere.models.user import User
from booksphere.security.password_hasher import hash_password
from booksphere.services.auth.email_verification_service import EmailVerificationService
from tests.unit.services.fakes_email_verification import (
    FakeEmailVerificationRepository,
    FakeUserRepositoryForVerification,
)


@pytest.fixture
def user_repo():
    return FakeUserRepositoryForVerification()


@pytest.fixture
def verification_service(user_repo, monkeypatch):
    # send_verification_email.delay() would otherwise reach a real
    # Celery broker during a unit test.
    import booksphere.services.auth.email_verification_service as ev_module

    class FakeTask:
        def delay(self, **kwargs):
            pass

    monkeypatch.setattr(ev_module, "send_verification_email", FakeTask())

    return EmailVerificationService(FakeEmailVerificationRepository(), user_repo)


def _make_user(user_repo, verified=False):
    user = User(
        email="verify-test@example.com",
        password_hash=hash_password("correct-horse-battery-staple-1"),
        full_name="Verify Test",
        email_verified=verified,
    )
    user_repo.add(user)
    return user


class TestIssueToken:
    def test_creates_a_pending_token(self, verification_service, user_repo):
        user = _make_user(user_repo)
        verification_service.issue_token(user.id, "http://localhost:3000")

        token = next(iter(verification_service._tokens._tokens.values()))
        assert token.user_id == user.id
        assert token.used_at is None


class TestConfirmToken:
    def test_confirms_a_valid_token_and_marks_user_verified(
        self, verification_service, user_repo, monkeypatch
    ):
        import booksphere.services.auth.email_verification_service as ev_module

        monkeypatch.setattr(ev_module, "hash_token", lambda raw: raw)

        user = _make_user(user_repo)
        verification_service.issue_token(user.id, "http://localhost:3000")
        token = next(iter(verification_service._tokens._tokens.values()))

        verification_service.confirm_token(token.token_hash)

        assert user.email_verified is True
        assert token.used_at is not None

    def test_raises_not_found_for_unknown_token(self, verification_service):
        with pytest.raises(VerificationTokenNotFoundError):
            verification_service.confirm_token("nonexistent-token")

    def test_raises_expired_for_past_expiry(self, verification_service, user_repo, monkeypatch):
        import booksphere.services.auth.email_verification_service as ev_module
        from datetime import datetime, timedelta, timezone

        monkeypatch.setattr(ev_module, "hash_token", lambda raw: raw)

        user = _make_user(user_repo)
        verification_service.issue_token(user.id, "http://localhost:3000")
        token = next(iter(verification_service._tokens._tokens.values()))
        token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        with pytest.raises(VerificationTokenExpiredError):
            verification_service.confirm_token(token.token_hash)

    def test_raises_expired_for_already_used_token(
        self, verification_service, user_repo, monkeypatch
    ):
        import booksphere.services.auth.email_verification_service as ev_module

        monkeypatch.setattr(ev_module, "hash_token", lambda raw: raw)

        user = _make_user(user_repo)
        verification_service.issue_token(user.id, "http://localhost:3000")
        token = next(iter(verification_service._tokens._tokens.values()))

        verification_service.confirm_token(token.token_hash)  # first use succeeds

        with pytest.raises(VerificationTokenExpiredError):
            verification_service.confirm_token(token.token_hash)  # second use fails


class TestResendVerification:
    def test_raises_when_already_verified(self, verification_service, user_repo):
        user = _make_user(user_repo, verified=True)

        with pytest.raises(EmailAlreadyVerifiedError):
            verification_service.resend_verification(user.id, "http://localhost:3000")

    def test_invalidates_prior_tokens_before_issuing_a_new_one(
        self, verification_service, user_repo, monkeypatch
    ):
        import booksphere.services.auth.email_verification_service as ev_module

        monkeypatch.setattr(ev_module, "hash_token", lambda raw: raw)

        user = _make_user(user_repo)
        verification_service.issue_token(user.id, "http://localhost:3000")
        first_token = next(iter(verification_service._tokens._tokens.values()))

        verification_service.resend_verification(user.id, "http://localhost:3000")

        assert first_token.used_at is not None
        all_tokens = list(verification_service._tokens._tokens.values())
        assert len(all_tokens) == 2
        second_token = [t for t in all_tokens if t.used_at is None][0]
        assert second_token.token_hash != first_token.token_hash
