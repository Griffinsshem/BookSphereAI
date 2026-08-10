"""
Generic repository base.

Services depend on repositories, never on SQLAlchemy directly — this
is the boundary that keeps our business logic testable without a real
database (services can be unit-tested against a fake repository) and
keeps query logic in exactly one layer.
"""
from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from booksphere.extensions import db

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def get_by_id(self, entity_id: UUID) -> ModelT | None:
        return db.session.get(self.model, entity_id)

    def add(self, entity: ModelT) -> None:
        db.session.add(entity)

    def commit(self) -> None:
        db.session.commit()

    def delete(self, entity: ModelT) -> None:
        db.session.delete(entity)
