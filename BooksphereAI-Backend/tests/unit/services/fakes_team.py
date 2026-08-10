"""Fake in-memory repositories for unit-testing InviteService and
MembershipService without a database."""
from __future__ import annotations
import uuid


class FakeInviteRepository:
    def __init__(self):
        self._invites: dict = {}

    def add(self, invite):
        if invite.id is None:
            invite.id = uuid.uuid4()
        self._invites[invite.id] = invite

    def commit(self):
        pass

    def get_by_token_hash(self, token_hash):
        return next((i for i in self._invites.values() if i.token_hash == token_hash), None)

    def get_pending_for_org_and_email(self, organization_id, email):
        return next(
            (
                i
                for i in self._invites.values()
                if i.organization_id == organization_id
                and i.email == email
                and i.status == "pending"
            ),
            None,
        )

    def list_pending_for_organization(self, organization_id):
        return [
            i
            for i in self._invites.values()
            if i.organization_id == organization_id and i.status == "pending"
        ]

    def get_for_organization(self, invite_id, organization_id):
        invite = self._invites.get(invite_id)
        if invite is None or invite.organization_id != organization_id:
            return None
        return invite


class FakeMembershipRepositoryForTeam:
    def __init__(self):
        self._memberships: list = []

    def add(self, membership):
        self._memberships.append(membership)

    def commit(self):
        pass

    def delete(self, membership):
        self._memberships.remove(membership)

    def get_for_user_and_org(self, user_id, organization_id):
        return next(
            (
                m
                for m in self._memberships
                if m.user_id == user_id and m.organization_id == organization_id
            ),
            None,
        )

    def list_for_organization_ordered(self, organization_id):
        return [m for m in self._memberships if m.organization_id == organization_id]

    def count_owners_for_organization(self, organization_id):
        return sum(
            1
            for m in self._memberships
            if m.organization_id == organization_id and m.role == "owner"
        )


class FakeUserRepositoryForTeam:
    def __init__(self):
        self._users: dict = {}

    def add(self, user):
        if user.id is None:
            user.id = uuid.uuid4()
        self._users[user.id] = user

    def get_by_id(self, user_id):
        return self._users.get(user_id)
