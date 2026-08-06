"""
ResourceService: all business logic for creating/reading/updating/
deleting Resources and their WorkingHours. Routes call this and
nothing else -- no queries, no validation logic in the routes module.
"""
from __future__ import annotations
from datetime import time
from uuid import UUID

from booksphere.domain.resources.exceptions import ResourceNotFoundError
from booksphere.domain.resources.value_objects import (
    validate_resource_type,
    validate_working_hours_window,
)
from booksphere.models.resource import Resource
from booksphere.models.working_hours import WorkingHours
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.working_hours_repository import WorkingHoursRepository


class ResourceService:
    def __init__(
        self, resource_repo: ResourceRepository, working_hours_repo: WorkingHoursRepository
    ) -> None:
        self._resources = resource_repo
        self._working_hours = working_hours_repo

    def create_resource(
        self,
        organization_id: UUID,
        resource_type: str,
        name: str,
        description: str | None = None,
        capacity: int | None = None,
        user_id: UUID | None = None,
    ) -> Resource:
        validate_resource_type(resource_type)

        resource = Resource(
            organization_id=organization_id,
            resource_type=resource_type,
            name=name.strip(),
            description=description,
            capacity=capacity,
            user_id=user_id,
        )
        self._resources.add(resource)
        self._resources.commit()
        return resource

    def get_resource(self, resource_id: UUID, organization_id: UUID) -> Resource:
        resource = self._resources.get_for_organization(resource_id, organization_id)
        if resource is None:
            raise ResourceNotFoundError()
        return resource

    def update_resource(
        self,
        resource_id: UUID,
        organization_id: UUID,
        **fields: object,
    ) -> Resource:
        resource = self.get_resource(resource_id, organization_id)

        # Explicit allow-list of updatable fields -- this is what
        # prevents mass assignment. A caller cannot pass
        # organization_id or id through **fields and have it silently
        # applied, because anything not in this tuple is ignored.
        allowed_fields = {"name", "description", "capacity", "is_active"}
        for key, value in fields.items():
            if key in allowed_fields and value is not None:
                setattr(resource, key, value)

        self._resources.commit()
        return resource

    def deactivate_resource(self, resource_id: UUID, organization_id: UUID) -> Resource:
        resource = self.get_resource(resource_id, organization_id)
        resource.is_active = False
        self._resources.commit()
        return resource

    def add_working_hours(
        self,
        resource_id: UUID,
        organization_id: UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
    ) -> WorkingHours:
        # Confirms the resource belongs to this org BEFORE attaching
        # working hours to it -- prevents attaching working hours to
        # another tenant's resource via a guessed resource_id.
        self.get_resource(resource_id, organization_id)

        validate_working_hours_window(day_of_week, start_time, end_time)

        window = WorkingHours(
            resource_id=resource_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        self._working_hours.add(window)
        self._working_hours.commit()
        return window

    def list_working_hours(self, resource_id: UUID, organization_id: UUID) -> list[WorkingHours]:
        self.get_resource(resource_id, organization_id)
        return self._working_hours.list_for_resource(resource_id)
