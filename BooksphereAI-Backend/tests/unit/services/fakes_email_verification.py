from __future__ import annotations
import uuid


class FakeEmailVerificationRepository:
    def __init__(self):
        self._tokens: dict = {}

    def add(self, token):
        if token.id is None:
            token.id = uuid.uuid4()
        self._tokens[token.id] = token

    def commit(self):
        pass

    def get_by_token_hash(self, token_hash):
        return next((t for t in self._tokens.values() if t.token_hash == token_hash), None)

    def invalidate_all_for_user(self, user_id):
        from datetime import datetime, timezone

        for token in self._tokens.values():
            if token.user_id == user_id and token.used_at is None:
                token.used_at = datetime.now(timezone.utc)


class FakeUserRepositoryForVerification:
    def __init__(self):
        self._users: dict = {}

    def add(self, user):
        if user.id is None:
            user.id = uuid.uuid4()
        self._users[user.id] = user

    def get_by_id(self, user_id):
        return self._users.get(user_id)
