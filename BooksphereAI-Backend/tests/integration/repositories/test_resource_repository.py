"""
Integration tests: real Postgres, real constraints and query behavior.
"""
from __future__ import annotations
import uuid

from booksphere.models.organization import Organization
from booksphere.models.resource import Resource
from booksphere.repositories.resource_repository import ResourceRepository


def _make_org(db_session, name="Test Org"):
    # uuid4, not id(object()) -- id() reuses memory addresses once an
    # object is garbage collected, so two short-lived objects created
    # in the same test CAN produce the same "unique" value. Rare
    # enough to pass most of the time, which is exactly what made this
    # a confusing, intermittent failure rather than a reliable one.
    org = Organization(name=name, slug=f"test-org-{uuid.uuid4().hex[:12]}")
    db_session.add(org)
    db_session.flush()
    return org


class TestResourceRepository:
    def test_get_for_organization_finds_own_resource(self, db_session):
        org = _make_org(db_session)
        resource = Resource(organization_id=org.id, resource_type="room", name="Room 1")
        db_session.add(resource)
        db_session.flush()

        repo = ResourceRepository()
        found = repo.get_for_organization(resource.id, org.id)

        assert found is not None
        assert found.id == resource.id

    def test_get_for_organization_returns_none_for_cross_tenant_id(self, db_session):
        """This is the actual database-level proof of the IDOR
        defense: a resource that genuinely exists, but under a
        DIFFERENT organization_id, must be invisible to this query --
        proving the tenant scoping is enforced by the query itself,
        not just application logic that could be bypassed."""
        org_a = _make_org(db_session, "Org A")
        org_b = _make_org(db_session, "Org B")
        resource = Resource(organization_id=org_a.id, resource_type="room", name="Org A's Room")
        db_session.add(resource)
        db_session.flush()

        repo = ResourceRepository()
        found = repo.get_for_organization(resource.id, org_b.id)

        assert found is None

    def test_list_for_organization_filters_by_resource_type(self, db_session):
        org = _make_org(db_session)
        db_session.add(Resource(organization_id=org.id, resource_type="room", name="Room 1"))
        db_session.add(Resource(organization_id=org.id, resource_type="staff", name="Staff 1"))
        db_session.flush()

        repo = ResourceRepository()
        pagination = repo.list_for_organization(org.id, resource_type="room")

        assert pagination.total == 1
        assert pagination.items[0].resource_type == "room"
