"""Domain-level exceptions for the booking engine."""
from __future__ import annotations

from booksphere.domain.users.exceptions import DomainError


class BookingNotFoundError(DomainError):
    pass


class SlotUnavailableError(DomainError):
    """Raised when the requested slot is no longer free -- either it
    was never free, or a concurrent request took it first."""


class BookingInThePastError(DomainError):
    pass


class ResourceNotLinkedToServiceError(DomainError):
    """The resource specified doesn't actually fulfill the requested
    service (no row in service_resources) -- prevents booking a
    massage room for a haircut, or a resource from an entirely
    different service than the client claims."""


class OutsideWorkingHoursError(DomainError):
    pass


class BookingAlreadyCancelledError(DomainError):
    pass
