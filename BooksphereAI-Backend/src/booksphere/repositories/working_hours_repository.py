from __future__ import annotations
from uuid import UUID

from booksphere.models.working_hours import WorkingHours
from booksphere.repositories.base import BaseRepository


class WorkingHoursRepository(BaseRepository[WorkingHours]):
    model = WorkingHours

    def list_for_resource(self, resource_id: UUID) -> list[WorkingHours]:
        return (
            WorkingHours.query.filter_by(resource_id=resource_id)
            .order_by(WorkingHours.day_of_week, WorkingHours.start_time)
            .all()
        )
