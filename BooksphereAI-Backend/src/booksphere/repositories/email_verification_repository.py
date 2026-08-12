from __future__ import annotations
from uuid import UUID

from booksphere.models.email_verification_token import EmailVerificationToken
from booksphere.repositories.base import BaseRepository


class EmailVerificationRepository(BaseRepository[EmailVerificationToken]):
    model = EmailVerificationToken

    def get_by_token_hash(self, token_hash: str) -> EmailVerificationToken | None:
        return EmailVerificationToken.query.filter_by(token_hash=token_hash).first()

    def invalidate_all_for_user(self, user_id: UUID) -> None:
        """Marks every existing token for this user as used -- called
        before issuing a fresh one on resend, so an old email link
        can never be used after a newer one was requested (avoids a
        user having multiple simultaneously-valid verification links
        floating around inboxes)."""
        from datetime import datetime, timezone

        EmailVerificationToken.query.filter_by(user_id=user_id, used_at=None).update(
            {"used_at": datetime.now(timezone.utc)}
        )
