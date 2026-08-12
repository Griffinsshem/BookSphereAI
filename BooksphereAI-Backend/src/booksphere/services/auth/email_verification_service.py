"""
EmailVerificationService: issue, resend, and confirm email-verification
tokens. Same architectural shape as InviteService -- token generation,
hash-at-rest storage, single-use enforcement, Celery-based async
delivery.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import UUID

from booksphere.domain.users.exceptions import (
    EmailAlreadyVerifiedError,
    VerificationTokenExpiredError,
    VerificationTokenNotFoundError,
)
from booksphere.repositories.email_verification_repository import EmailVerificationRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.security.audit_logger import log_security_event
from booksphere.security.tokens import generate_opaque_token, hash_token
from booksphere.tasks.email_tasks import send_verification_email

_TOKEN_EXPIRY_HOURS = 24


class EmailVerificationService:
    def __init__(
        self, verification_repo: EmailVerificationRepository, user_repo: UserRepository
    ) -> None:
        self._tokens = verification_repo
        self._users = user_repo

    def issue_token(self, user_id: UUID, frontend_base_url: str) -> None:
        """Creates a fresh token and enqueues the email. Used both
        right after registration AND by the resend endpoint -- resend
        additionally invalidates prior tokens first (see
        resend_verification below), registration doesn't need to
        since a brand-new user has none yet."""
        user = self._users.get_by_id(user_id)
        if user is None:
            return

        raw_token = generate_opaque_token()
        from booksphere.models.email_verification_token import EmailVerificationToken

        token_row = EmailVerificationToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRY_HOURS),
        )
        self._tokens.add(token_row)
        self._tokens.commit()

        verify_url = f"{frontend_base_url}/verify-email/{raw_token}"
        send_verification_email.delay(
            to_email=user.email, full_name=user.full_name, verify_url=verify_url
        )

    def resend_verification(self, user_id: UUID, frontend_base_url: str) -> None:
        user = self._users.get_by_id(user_id)
        if user is None:
            return
        if user.email_verified:
            raise EmailAlreadyVerifiedError()

        # Invalidate any still-pending tokens first -- prevents a
        # user (or an attacker who somehow saw an old email) from
        # using a stale link after a newer one was requested.
        self._tokens.invalidate_all_for_user(user_id)
        self._tokens.commit()

        self.issue_token(user_id, frontend_base_url)

        log_security_event("verification_email_resent", user_id=str(user_id))

    def confirm_token(self, raw_token: str) -> None:
        token_hash = hash_token(raw_token)
        token_row = self._tokens.get_by_token_hash(token_hash)

        if token_row is None:
            raise VerificationTokenNotFoundError()
        if token_row.used_at is not None or token_row.expires_at < datetime.now(timezone.utc):
            raise VerificationTokenExpiredError()

        user = self._users.get_by_id(token_row.user_id)
        if user is None:
            raise VerificationTokenNotFoundError()

        user.email_verified = True
        token_row.used_at = datetime.now(timezone.utc)
        self._tokens.commit()

        log_security_event("email_verified", user_id=str(user.id))
