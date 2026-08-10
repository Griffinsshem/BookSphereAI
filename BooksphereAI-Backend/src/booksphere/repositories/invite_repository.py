from __future__ import annotations
from uuid import UUID

from booksphere.models.organization_invite import OrganizationInvite
from booksphere.repositories.base import BaseRepository


class InviteRepository(BaseRepository[OrganizationInvite]):
    model = OrganizationInvite

    def get_by_token_hash(self, token_hash: str) -> OrganizationInvite | None:
        return OrganizationInvite.query.filter_by(token_hash=token_hash).first()

    def get_pending_for_org_and_email(
        self, organization_id: UUID, email: str
    ) -> OrganizationInvite | None:
        return OrganizationInvite.query.filter_by(
            organization_id=organization_id, email=email, status="pending"
        ).first()

    def list_pending_for_organization(self, organization_id: UUID) -> list[OrganizationInvite]:
        return (
            OrganizationInvite.query.filter_by(organization_id=organization_id, status="pending")
            .order_by(OrganizationInvite.created_at.desc())
            .all()
        )

    def get_for_organization(
        self, invite_id: UUID, organization_id: UUID
    ) -> OrganizationInvite | None:
        # Same IDOR-safe pattern used throughout the project.
        return OrganizationInvite.query.filter_by(
            id=invite_id, organization_id=organization_id
        ).first()
