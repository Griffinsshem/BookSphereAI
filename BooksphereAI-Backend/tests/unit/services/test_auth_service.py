"""
Unit tests for AuthService — no Flask app, no database. Pure business
logic against fake repositories.
"""
from __future__ import annotations

import pytest

from booksphere.domain.users.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from booksphere.services.auth.auth_service import AuthService
from tests.unit.services.fakes import (
    FakeMembershipRepository,
    FakeOrganizationRepository,
    FakeRefreshTokenRepository,
    FakeUserRepository,
)


class _FakeEmailVerificationService:
    """Records calls instead of touching a real database -- register()
    calls issue_token() as a side effect, which this fixture needs to
    accept without requiring EmailVerificationRepository or a real
    user row to exist."""

    def __init__(self):
        self.issued_for = []

    def issue_token(self, user_id, frontend_base_url):
        self.issued_for.append(user_id)


@pytest.fixture
def auth_service(monkeypatch):
    # AuthService.register() flushes via booksphere.extensions.db,
    # which doesn't exist in this fake, DB-less context. We patch it
    # to a no-op here specifically, since the fakes assign IDs
    # themselves on .add() rather than relying on a DB flush.
    import booksphere.services.auth.auth_service as auth_module

    class _FakeDbSession:
        def flush(self):
            pass

    class _FakeDb:
        session = _FakeDbSession()

    monkeypatch.setattr(
        auth_module, "db", _FakeDb(), raising=False
    )

    service = AuthService(
        user_repo=FakeUserRepository(),
        org_repo=FakeOrganizationRepository(),
        membership_repo=FakeMembershipRepository(),
        refresh_token_repo=FakeRefreshTokenRepository(),
        email_verification_service=_FakeEmailVerificationService(),
    )
    return service


class TestRegister:
    def test_creates_user_and_organization(self, auth_service, app):
        with app.app_context():
            user, org = auth_service.register(
                email="Owner@Example.com",
                password="correct-horse-battery-staple-1",
                full_name="Ada Lovelace",
                organization_name="Acme Hotel",
            )

        # Email is normalized to lowercase on write, so future
        # lookups don't depend on the caller's casing.
        assert user.email == "owner@example.com"
        assert org.name == "Acme Hotel"
        assert org.slug == "acme-hotel"

    def test_rejects_duplicate_email(self, auth_service, app):
        with app.app_context():
            auth_service.register(
                "dup@example.com", "correct-horse-battery-staple-1", "A", "Org A"
            )
            with pytest.raises(EmailAlreadyRegisteredError):
                auth_service.register(
                    "dup@example.com", "another-strong-password-2", "B", "Org B"
                )

    def test_deduplicates_organization_slug(self, auth_service, app):
        with app.app_context():
            _, org_a = auth_service.register(
                "a@example.com", "correct-horse-battery-staple-1", "A", "Acme Hotel"
            )
            _, org_b = auth_service.register(
                "b@example.com", "correct-horse-battery-staple-1", "B", "Acme Hotel"
            )

        assert org_a.slug != org_b.slug
        assert org_b.slug.startswith("acme-hotel-")


class TestLogin:
    def test_succeeds_with_correct_credentials(self, auth_service, app):
        with app.app_context():
            auth_service.register(
                "login@example.com", "correct-horse-battery-staple-1", "A", "Org"
            )
            user, tokens = auth_service.login(
                "login@example.com", "correct-horse-battery-staple-1"
            )

        assert user.email == "login@example.com"
        assert tokens.access_token
        assert tokens.raw_refresh_token

    def test_rejects_wrong_password(self, auth_service, app):
        with app.app_context():
            auth_service.register(
                "wrongpw@example.com", "correct-horse-battery-staple-1", "A", "Org"
            )
            with pytest.raises(InvalidCredentialsError):
                auth_service.login("wrongpw@example.com", "not-the-right-password")

    def test_rejects_unknown_email(self, auth_service, app):
        with app.app_context():
            with pytest.raises(InvalidCredentialsError):
                auth_service.login("nobody@example.com", "irrelevant-password-1")

    def test_error_identical_for_wrong_password_and_unknown_email(
        self, auth_service, app
    ):
        """Security-critical assertion: both failure modes must raise
        the exact same exception type/message so a caller can't
        enumerate valid emails by distinguishing the two cases."""
        with app.app_context():
            auth_service.register(
                "known@example.com", "correct-horse-battery-staple-1", "A", "Org"
            )

            wrong_password_error = None
            unknown_email_error = None

            try:
                auth_service.login("known@example.com", "wrong-password-here")
            except InvalidCredentialsError as e:
                wrong_password_error = str(e)

            try:
                auth_service.login("unknown@example.com", "wrong-password-here")
            except InvalidCredentialsError as e:
                unknown_email_error = str(e)

        assert wrong_password_error == unknown_email_error
