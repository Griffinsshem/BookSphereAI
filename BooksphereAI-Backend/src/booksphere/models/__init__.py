"""
Ensures every model module is imported, so SQLAlchemy's metadata
(and therefore Alembic's autogenerate) always sees the complete
schema -- regardless of whether some other module happens to import
a given model transitively.

Without this, a model that isn't yet referenced by any repository/
service/route (exactly the situation with a freshly-added model like
Booking, before its own service layer exists) is invisible to
`flask db migrate`, which silently reports "No changes detected"
instead of an error -- a easy trap to fall into more than once.
"""
from __future__ import annotations

from booksphere.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from booksphere.models.booking import Booking
from booksphere.models.email_verification_token import EmailVerificationToken
from booksphere.models.organization import Organization
from booksphere.models.organization_invite import OrganizationInvite
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.models.refresh_token import RefreshToken
from booksphere.models.resource import Resource
from booksphere.models.service import Service
from booksphere.models.service_resource import ServiceResource
from booksphere.models.user import User
from booksphere.models.working_hours import WorkingHours

__all__ = [
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "Booking",
    "EmailVerificationToken",
    "Organization",
    "OrganizationInvite",
    "OrganizationMembership",
    "RefreshToken",
    "Resource",
    "Service",
    "ServiceResource",
    "User",
    "WorkingHours",
]
