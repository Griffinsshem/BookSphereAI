from __future__ import annotations
from uuid import UUID

from booksphere.models.refresh_token import RefreshToken
from booksphere.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return RefreshToken.query.filter_by(token_hash=token_hash).first()

    def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user — used on
        password change or suspected compromise, to force re-login on
        all devices."""
        from datetime import datetime, timezone

        RefreshToken.query.filter_by(user_id=user_id, revoked_at=None).update(
            {"revoked_at": datetime.now(timezone.utc)}
        )
