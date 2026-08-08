from __future__ import annotations
from booksphere.domain.users.exceptions import DomainError


class InvalidTimezoneError(DomainError):
    pass


class OrganizationNotFoundError(DomainError):
    pass
