"""
RefreshToken: DB-backed, hashed, revocable refresh tokens.

We deliberately do NOT use JWT for refresh tokens (only for access
tokens). A JWT refresh token can't be individually revoked without a
denylist that defeats the point of using a stateless token in the
first place — so refresh tokens are opaque random strings, stored here
as a hash, checked against the DB on every /refresh call. This is
what makes rotation-on-use and revocation-on-logout actually work.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import UUIDPrimaryKeyMixin


class RefreshToken(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        """A token is usable only if neither expired nor revoked."""
        from datetime import timezone

        now = datetime.now(timezone.utc)
        return self.revoked_at is None and self.expires_at > now
