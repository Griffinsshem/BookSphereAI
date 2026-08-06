from __future__ import annotations
from datetime import time
import uuid

import pytest

from booksphere.domain.resources.exceptions import (
    InvalidResourceTypeError,
    InvalidWorkingHoursError,
    ResourceNotFoundError,
)
from booksphere.services.catalog.resource_service import ResourceService
from tests.unit.services.fakes_catalog import FakeResourceRepository, FakeWorkingHoursRepository


@pytest.fixture
def resource_service():
    return ResourceService(FakeResourceRepository(), FakeWorkingHoursRepository())


class TestCreateResource:
    def test_creates_resource_with_valid_type(self, resource_service):
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Massage Room 1"
        )
        assert resource.resource_type == "room"
        assert resource.name == "Massage Room 1"
        assert resource.organization_id == org_id

    def test_rejects_invalid_resource_type(self, resource_service):
        with pytest.raises(InvalidResourceTypeError):
            resource_service.create_resource(
                organization_id=uuid.uuid4(), resource_type="spaceship", name="Nope"
            )

    def test_strips_whitespace_from_name(self, resource_service):
        resource = resource_service.create_resource(
            organization_id=uuid.uuid4(), resource_type="room", name="  Padded Name  "
        )
        assert resource.name == "Padded Name"


class TestGetResource:
    def test_raises_when_not_found(self, resource_service):
        with pytest.raises(ResourceNotFoundError):
            resource_service.get_resource(uuid.uuid4(), uuid.uuid4())

    def test_raises_for_cross_tenant_access(self, resource_service):
        """Security-critical: a resource from org A must be invisible
        (NotFoundError, not a different error) when queried with org
        B's organization_id -- this is the IDOR defense at the
        service layer, one level above the repository-level defense
        already tested in the integration suite."""
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_a, resource_type="room", name="Org A's Room"
        )

        with pytest.raises(ResourceNotFoundError):
            resource_service.get_resource(resource.id, org_b)


class TestUpdateResource:
    def test_updates_allowed_fields(self, resource_service):
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Original Name"
        )

        updated = resource_service.update_resource(resource.id, org_id, name="New Name")

        assert updated.name == "New Name"

    def test_ignores_disallowed_fields(self, resource_service):
        """Proves the mass-assignment defense: a field not on the
        allow-list (e.g. attempting to overwrite `id`) is silently
        ignored, even if a caller manages to smuggle it into the
        keyword arguments -- only fields explicitly listed in
        `allowed_fields` inside update_resource() are ever applied.
        (organization_id itself can't be tested this way since it's
        already a required positional parameter on this method, not
        reachable via **fields -- the schema layer is the first line
        of defense against that specific field, tested separately in
        the API layer.)"""
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Room"
        )
        original_id = resource.id
        smuggled_id = uuid.uuid4()

        updated = resource_service.update_resource(
            resource.id, org_id, id=smuggled_id, name="Renamed"
        )

        assert updated.id == original_id  # unchanged -- "id" was ignored
        assert updated.name == "Renamed"  # allowed field did change


class TestDeactivateResource:
    def test_sets_is_active_false(self, resource_service):
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Room"
        )

        deactivated = resource_service.deactivate_resource(resource.id, org_id)

        assert deactivated.is_active is False


class TestWorkingHours:
    def test_add_working_hours_for_own_resource(self, resource_service):
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Room"
        )

        window = resource_service.add_working_hours(
            resource.id, org_id, day_of_week=0, start_time=time(9, 0), end_time=time(17, 0)
        )

        assert window.day_of_week == 0

    def test_rejects_working_hours_for_cross_tenant_resource(self, resource_service):
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_a, resource_type="room", name="Org A's Room"
        )

        with pytest.raises(ResourceNotFoundError):
            resource_service.add_working_hours(
                resource.id, org_b, day_of_week=0, start_time=time(9, 0), end_time=time(17, 0)
            )

    def test_rejects_invalid_window(self, resource_service):
        org_id = uuid.uuid4()
        resource = resource_service.create_resource(
            organization_id=org_id, resource_type="room", name="Room"
        )

        with pytest.raises(InvalidWorkingHoursError):
            resource_service.add_working_hours(
                resource.id, org_id, day_of_week=0, start_time=time(17, 0), end_time=time(9, 0)
            )
