"""
Fake in-memory repositories for unit-testing ResourceService and
OfferingService without a database.
"""
from __future__ import annotations
import uuid


class FakeResourceRepository:
    def __init__(self):
        self._resources: dict = {}

    def add(self, resource):
        if resource.id is None:
            resource.id = uuid.uuid4()
        self._resources[resource.id] = resource

    def commit(self):
        pass

    def get_for_organization(self, resource_id, organization_id):
        resource = self._resources.get(resource_id)
        if resource is None or resource.organization_id != organization_id:
            return None
        return resource

    def list_for_organization(self, organization_id, **kwargs):
        return [r for r in self._resources.values() if r.organization_id == organization_id]


class FakeWorkingHoursRepository:
    def __init__(self):
        self._windows: list = []

    def add(self, window):
        self._windows.append(window)

    def commit(self):
        pass

    def list_for_resource(self, resource_id):
        return [w for w in self._windows if w.resource_id == resource_id]


class FakeServiceRepository:
    def __init__(self):
        self._services: dict = {}

    def add(self, service):
        if service.id is None:
            service.id = uuid.uuid4()
        self._services[service.id] = service

    def commit(self):
        pass

    def get_for_organization(self, service_id, organization_id):
        service = self._services.get(service_id)
        if service is None or service.organization_id != organization_id:
            return None
        return service


class FakeServiceResourceRepository:
    def __init__(self):
        self._links: list = []

    def add(self, link):
        self._links.append(link)

    def commit(self):
        pass

    def link_exists(self, service_id, resource_id):
        return any(
            link.service_id == service_id and link.resource_id == resource_id
            for link in self._links
        )
