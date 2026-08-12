"""
EmailVerificationToken: hashed, single-use, short-lived (24h) token
proving control of the account's email address. Identical security
pattern to RefreshToken and OrganizationInvite -- raw token only ever
exists in the email link, never persisted; only its hash is stored.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from booksphere.extensions import db
from booksphere.models.base import UUIDPrimaryKeyMixin


class EmailVerificationToken(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "email_verification_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
