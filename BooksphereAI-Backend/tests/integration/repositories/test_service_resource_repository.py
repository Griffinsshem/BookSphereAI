"""
Integration test proving uq_service_resource is a REAL database
constraint, not just an application-level assumption.
"""
from __future__ import annotations
import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from booksphere.models.organization import Organization
from booksphere.models.resource import Resource
from booksphere.models.service import Service
from booksphere.models.service_resource import ServiceResource


class TestServiceResourceConstraint:
    def test_duplicate_link_rejected_by_db_constraint(self, db_session):
        org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:12]}")
        db_session.add(org)
        db_session.flush()

        service = Service(
            organization_id=org.id, name="Massage", duration_minutes=60, price_cents=8000
        )
        resource = Resource(organization_id=org.id, resource_type="staff", name="Masseuse")
        db_session.add(service)
        db_session.add(resource)
        db_session.flush()

        db_session.add(ServiceResource(service_id=service.id, resource_id=resource.id))
        db_session.flush()

        db_session.add(ServiceResource(service_id=service.id, resource_id=resource.id))
        with pytest.raises(IntegrityError):
            db_session.flush()
