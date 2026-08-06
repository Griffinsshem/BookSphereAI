from __future__ import annotations
import uuid

import pytest

from booksphere.domain.resources.exceptions import (
    CrossTenantResourceLinkError,
    InvalidServiceDurationError,
    ServiceNotFoundError,
)
from booksphere.services.catalog.offering_service import OfferingService
from tests.unit.services.fakes_catalog import (
    FakeResourceRepository,
    FakeServiceRepository,
    FakeServiceResourceRepository,
)


@pytest.fixture
def offering_service():
    return OfferingService(
        FakeServiceRepository(), FakeResourceRepository(), FakeServiceResourceRepository()
    )


class TestCreateService:
    def test_creates_service_with_valid_duration(self, offering_service):
        org_id = uuid.uuid4()
        service = offering_service.create_service(
            organization_id=org_id, name="Massage", duration_minutes=60, price_cents=8000
        )
        assert service.duration_minutes == 60
        assert service.price_cents == 8000
        assert service.currency == "USD"

    def test_rejects_zero_duration(self, offering_service):
        with pytest.raises(InvalidServiceDurationError):
            offering_service.create_service(
                organization_id=uuid.uuid4(), name="Bad", duration_minutes=0, price_cents=100
            )

    def test_normalizes_currency_to_uppercase(self, offering_service):
        service = offering_service.create_service(
            organization_id=uuid.uuid4(),
            name="Massage",
            duration_minutes=60,
            price_cents=8000,
            currency="usd",
        )
        assert service.currency == "USD"


class TestLinkResource:
    def test_links_service_to_resource_in_same_org(self, offering_service):
        org_id = uuid.uuid4()
        service = offering_service.create_service(
            organization_id=org_id, name="Massage", duration_minutes=60, price_cents=8000
        )
        # Build the resource directly via the fake repo the fixture
        # already holds, so it shares the same underlying store.
        from booksphere.models.resource import Resource

        resource_obj = Resource(
            organization_id=org_id, resource_type="staff", name="Masseuse"
        )
        offering_service._resources.add(resource_obj)

        link = offering_service.link_resource(service.id, resource_obj.id, org_id)

        assert link.service_id == service.id
        assert link.resource_id == resource_obj.id

    def test_rejects_linking_resource_from_different_org(self, offering_service):
        """Security-critical: proves CrossTenantResourceLinkError is
        raised when attempting to link a service to a resource that
        belongs to a DIFFERENT organization -- this is the check that
        stops a service in org A from ever referencing org B's
        physical resources."""
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()

        service = offering_service.create_service(
            organization_id=org_a, name="Massage", duration_minutes=60, price_cents=8000
        )

        from booksphere.models.resource import Resource

        other_orgs_resource = Resource(
            organization_id=org_b, resource_type="staff", name="Org B's Staff"
        )
        offering_service._resources.add(other_orgs_resource)

        with pytest.raises(CrossTenantResourceLinkError):
            offering_service.link_resource(service.id, other_orgs_resource.id, org_a)

    def test_raises_when_service_not_found(self, offering_service):
        with pytest.raises(ServiceNotFoundError):
            offering_service.link_resource(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
