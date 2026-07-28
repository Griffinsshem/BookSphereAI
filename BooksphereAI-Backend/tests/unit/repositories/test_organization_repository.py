"""Small gap-filling test: get_by_slug was written but never exercised."""
from __future__ import annotations

from booksphere.models.organization import Organization
from booksphere.repositories.organization_repository import OrganizationRepository


class TestOrganizationRepository:
    def test_get_by_slug_finds_existing_organization(self, db_session):
        org = Organization(name="Slug Test Org", slug="slug-test-org")
        db_session.add(org)
        db_session.flush()

        repo = OrganizationRepository()
        result = repo.get_by_slug("slug-test-org")

        assert result is not None
        assert result.id == org.id

    def test_get_by_slug_returns_none_when_absent(self, db_session):
        repo = OrganizationRepository()
        assert repo.get_by_slug("does-not-exist") is None
