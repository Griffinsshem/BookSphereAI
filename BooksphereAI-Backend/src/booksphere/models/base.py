"""
Shared model mixins.

Every table in BookSphere AI includes a UUID primary key and
created_at/updated_at timestamps. Rather than repeating those three
columns on every model (violates DRY, and risks inconsistency — e.g.
one model using server_default and another using a Python default),
they're defined once here and mixed into every model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key, generated server-side by PostgreSQL.

    Using PostgreSQL's own uuid_generate_v4() (via server_default)
    rather than generating the UUID in Python means the ID exists even
    for rows inserted outside the ORM (e.g. raw SQL migrations, bulk
    loads) and avoids a round-trip where Python has to invent an ID
    before knowing whether the row will actually be accepted.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Adds created_at/updated_at, both set and maintained by the DB.

    server_default=func.now() means the timestamp is assigned by
    PostgreSQL at insert time, not by the application server's clock —
    important once we run multiple app instances that could have
    slightly skewed clocks. onupdate=func.now() on updated_at means we
    never have to remember to touch it manually in application code.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
