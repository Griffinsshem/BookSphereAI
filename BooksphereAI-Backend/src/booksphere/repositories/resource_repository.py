from __future__ import annotations
from uuid import UUID

from booksphere.models.resource import Resource
from booksphere.repositories.base import BaseRepository


class ResourceRepository(BaseRepository[Resource]):
    model = Resource

    def list_for_organization(
        self,
        organization_id: UUID,
        resource_type: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        # Tenant scoping happens HERE, at the query level -- every
        # single caller of this method is guaranteed to only ever see
        # rows from one organization, regardless of what filters are
        # applied on top.
        query = Resource.query.filter_by(organization_id=organization_id)
        if resource_type is not None:
            query = query.filter_by(resource_type=resource_type)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(Resource.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_for_organization(self, resource_id: UUID, organization_id: UUID) -> Resource | None:
        # Deliberately filters by BOTH id and organization_id in one
        # query, rather than fetching by id and checking org_id in
        # Python -- a resource belonging to a different tenant simply
        # doesn't match this query and returns None, the same as a
        # resource that doesn't exist at all. This is what makes IDOR
        # (guessing another tenant's UUID) return a clean 404 instead
        # of leaking whether the ID exists.
        return Resource.query.filter_by(id=resource_id, organization_id=organization_id).first()
