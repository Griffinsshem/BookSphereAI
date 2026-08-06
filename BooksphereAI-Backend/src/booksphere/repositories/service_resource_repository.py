from __future__ import annotations
from uuid import UUID

from booksphere.models.service_resource import ServiceResource
from booksphere.repositories.base import BaseRepository


class ServiceResourceRepository(BaseRepository[ServiceResource]):
    model = ServiceResource

    def link_exists(self, service_id: UUID, resource_id: UUID) -> bool:
        return (
            ServiceResource.query.filter_by(
                service_id=service_id, resource_id=resource_id
            ).first()
            is not None
        )
