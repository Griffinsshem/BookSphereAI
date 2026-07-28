"""
Fake (in-memory) repositories for unit-testing AuthService without a
real database. Each fake implements the same interface the real
repository does, backed by a plain dict instead of SQLAlchemy.
"""
from __future__ import annotations
import uuid


class FakeUserRepository:
    def __init__(self):
        self._users: dict = {}

    def get_by_email(self, email):
        return next(
            (u for u in self._users.values() if u.email == email.lower()), None
        )

    def get_by_id(self, entity_id):
        return self._users.get(entity_id)

    def add(self, user):
        if user.id is None:
            user.id = uuid.uuid4()
        self._users[user.id] = user

    def commit(self):
        pass  # no-op — nothing to flush for an in-memory dict


class FakeOrganizationRepository:
    def __init__(self):
        self._orgs: dict = {}

    def slug_exists(self, slug):
        return any(o.slug == slug for o in self._orgs.values())

    def add(self, org):
        if org.id is None:
            org.id = uuid.uuid4()
        self._orgs[org.id] = org

    def commit(self):
        pass


class FakeMembershipRepository:
    def __init__(self):
        self._memberships: list = []

    def get_for_user_and_org(self, user_id, organization_id):
        return next(
            (
                m
                for m in self._memberships
                if m.user_id == user_id and m.organization_id == organization_id
            ),
            None,
        )

    def add(self, membership):
        self._memberships.append(membership)

    def commit(self):
        pass


class FakeRefreshTokenRepository:
    def __init__(self):
        self._tokens: dict = {}

    def get_by_token_hash(self, token_hash):
        return self._tokens.get(token_hash)

    def add(self, token):
        self._tokens[token.token_hash] = token

    def commit(self):
        pass
