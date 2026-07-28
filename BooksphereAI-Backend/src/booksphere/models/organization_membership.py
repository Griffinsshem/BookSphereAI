"""
OrganizationMembership: the join table that actually defines tenant
access. This is the single source of truth for "which organizations
can this user act in, and with what role."

Every future protected endpoint resolves authorization by querying
this table server-side — never by trusting a client-supplied
organization_id at face value.
"""
from __future__ import annotations
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationMembership(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped["User"] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship(back_populates="memberships")
