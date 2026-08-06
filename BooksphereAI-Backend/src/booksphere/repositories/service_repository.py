from __future__ import annotations
from uuid import UUID

from booksphere.models.service import Service
from booksphere.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    model = Service

    def list_for_organization(
        self,
        organization_id: UUID,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        query = Service.query.filter_by(organization_id=organization_id)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(Service.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_for_organization(self, service_id: UUID, organization_id: UUID) -> Service | None:
        return Service.query.filter_by(id=service_id, organization_id=organization_id).first()
