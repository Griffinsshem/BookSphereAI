"""
OfferingService: business logic for Service (the bookable offering)
and its links to Resources. Named "Offering" rather than "Service" to
avoid a naming collision with our own service-layer architecture
pattern -- the class manages Service model instances, but "Service"
as a class name here would be confusing next to "ResourceService" /
"AuthService" which follow the [Domain]Service naming convention.
"""
from __future__ import annotations
from uuid import UUID

from booksphere.domain.resources.exceptions import (
    CrossTenantResourceLinkError,
    ServiceNotFoundError,
)
from booksphere.domain.resources.value_objects import validate_service_duration
from booksphere.models.service import Service
from booksphere.models.service_resource import ServiceResource
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.service_repository import ServiceRepository
from booksphere.repositories.service_resource_repository import ServiceResourceRepository


class OfferingService:
    def __init__(
        self,
        service_repo: ServiceRepository,
        resource_repo: ResourceRepository,
        service_resource_repo: ServiceResourceRepository,
    ) -> None:
        self._services = service_repo
        self._resources = resource_repo
        self._service_resources = service_resource_repo

    def create_service(
        self,
        organization_id: UUID,
        name: str,
        duration_minutes: int,
        price_cents: int,
        currency: str = "USD",
        description: str | None = None,
    ) -> Service:
        validate_service_duration(duration_minutes)

        service = Service(
            organization_id=organization_id,
            name=name.strip(),
            description=description,
            duration_minutes=duration_minutes,
            price_cents=price_cents,
            currency=currency.upper(),
        )
        self._services.add(service)
        self._services.commit()
        return service

    def get_service(self, service_id: UUID, organization_id: UUID) -> Service:
        service = self._services.get_for_organization(service_id, organization_id)
        if service is None:
            raise ServiceNotFoundError()
        return service

    def update_service(self, service_id: UUID, organization_id: UUID, **fields: object) -> Service:
        service = self.get_service(service_id, organization_id)

        allowed_fields = {
            "name",
            "description",
            "duration_minutes",
            "price_cents",
            "currency",
            "is_active",
        }
        if "duration_minutes" in fields and fields["duration_minutes"] is not None:
            validate_service_duration(fields["duration_minutes"])

        for key, value in fields.items():
            if key in allowed_fields and value is not None:
                setattr(service, key, value)

        self._services.commit()
        return service

    def deactivate_service(self, service_id: UUID, organization_id: UUID) -> Service:
        service = self.get_service(service_id, organization_id)
        service.is_active = False
        self._services.commit()
        return service

    def link_resource(self, service_id: UUID, resource_id: UUID, organization_id: UUID) -> ServiceResource:
        # Both lookups are org-scoped -- this is the check that
        # prevents linking a service in org A to a resource in org B,
        # even though nothing at the database FK level would catch
        # that on its own.
        service = self.get_service(service_id, organization_id)
        resource = self._resources.get_for_organization(resource_id, organization_id)
        if resource is None:
            raise CrossTenantResourceLinkError(
                "Cannot link a service to a resource outside its organization."
            )

        if self._service_resources.link_exists(service.id, resource.id):
            existing = ServiceResource.query.filter_by(
                service_id=service.id, resource_id=resource.id
            ).first()
            return existing

        link = ServiceResource(service_id=service.id, resource_id=resource.id)
        self._service_resources.add(link)
        self._service_resources.commit()
        return link
