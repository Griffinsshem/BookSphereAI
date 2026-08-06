"""Domain-level exceptions for resources/services/working-hours."""
from __future__ import annotations

from booksphere.domain.users.exceptions import DomainError


class ResourceNotFoundError(DomainError):
    pass


class ServiceNotFoundError(DomainError):
    pass


class InvalidResourceTypeError(DomainError):
    pass


class InvalidWorkingHoursError(DomainError):
    pass


class CrossTenantResourceLinkError(DomainError):
    """Raised when attempting to link a service to a resource belonging
    to a different organization -- a tenant-isolation violation that
    must never be allowed to reach the database."""


class InvalidServiceDurationError(DomainError):
    pass
