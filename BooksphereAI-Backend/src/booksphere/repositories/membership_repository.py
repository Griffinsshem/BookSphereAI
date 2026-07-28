from __future__ import annotations
from uuid import UUID

from booksphere.models.organization_membership import OrganizationMembership
from booksphere.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[OrganizationMembership]):
    model = OrganizationMembership

    def get_for_user_and_org(
        self, user_id: UUID, organization_id: UUID
    ) -> OrganizationMembership | None:
        return OrganizationMembership.query.filter_by(
            user_id=user_id, organization_id=organization_id
        ).first()

    def list_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
        return OrganizationMembership.query.filter_by(user_id=user_id).all()
