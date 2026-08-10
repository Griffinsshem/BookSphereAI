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

    def list_for_organization_ordered(self, organization_id: UUID) -> list[OrganizationMembership]:
        # "owner" sorted first (alphabetically it already is: manager
        # < owner < staff would NOT put owner first, so an explicit
        # CASE ordering is used) -- a member list is most useful with
        # the owner shown at the top, then descending by seniority.
        from sqlalchemy import case

        role_order = case(
            (OrganizationMembership.role == "owner", 0),
            (OrganizationMembership.role == "manager", 1),
            (OrganizationMembership.role == "staff", 2),
            else_=3,
        )
        return (
            OrganizationMembership.query.filter_by(organization_id=organization_id)
            .order_by(role_order, OrganizationMembership.created_at)
            .all()
        )

    def count_owners_for_organization(self, organization_id: UUID) -> int:
        return OrganizationMembership.query.filter_by(
            organization_id=organization_id, role="owner"
        ).count()
