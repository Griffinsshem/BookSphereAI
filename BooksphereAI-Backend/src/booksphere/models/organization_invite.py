"""
OrganizationInvite: a pending (or resolved) invitation to join an
organization. Same hash-not-raw-value pattern as RefreshToken -- the
raw token only ever exists in the invite link sent to the invitee,
never persisted.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationInvite(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_invites"
    __table_args__ = (
        # PARTIAL unique index (WHERE status='pending'): only one
        # PENDING invite per (org, email) at a time. A previously
        # revoked/expired/accepted invite to the same email does NOT
        # block a fresh one -- only an existing pending invite does.
        # This is the same technique family as the booking exclusion
        # constraint: a database-level guarantee, not just an
        # application-level check that could be bypassed by a bug or
        # a second writer.
        Index(
            "uq_pending_invite_per_org_email",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    invited_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
