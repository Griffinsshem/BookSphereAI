from __future__ import annotations

from booksphere.models.organization import Organization
from booksphere.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def get_by_slug(self, slug: str) -> Organization | None:
        return Organization.query.filter_by(slug=slug).first()

    def slug_exists(self, slug: str) -> bool:
        return Organization.query.filter_by(slug=slug).first() is not None
