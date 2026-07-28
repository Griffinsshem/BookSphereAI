from __future__ import annotations

from booksphere.models.user import User
from booksphere.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email.lower()).first()
