"""
ServiceResource: join table -- which resources can fulfill a given
service. Explicit join table (not a JSON array column) so it stays
indexable/queryable as data grows -- "find all services this staff
member can perform" or "find all resources that can fulfill this
service" are both real queries the booking engine will need.
"""
from __future__ import annotations
import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booksphere.extensions import db
from booksphere.models.base import UUIDPrimaryKeyMixin


class ServiceResource(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "service_resources"
    __table_args__ = (
        UniqueConstraint("service_id", "resource_id", name="uq_service_resource"),
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False
    )

    service: Mapped["Service"] = relationship(back_populates="resource_links")
    resource: Mapped["Resource"] = relationship()
