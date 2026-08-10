"""
InviteService: create, list, revoke, and accept organization invites.

Email-enumeration defense: create_invite() behaves IDENTICALLY
whether or not the invited email already belongs to a registered
User -- the caller (an owner/manager inviting someone) never learns
that from this service's return value or any exception raised. This
mirrors the same defense we built into login() in Feature 1's
AuthService.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import UUID

from booksphere.domain.team.exceptions import (
    DuplicatePendingInviteError,
    InviteAlreadyAcceptedError,
    InviteExpiredError,
    InviteNotFoundError,
)
from booksphere.domain.team.value_objects import INVITE_EXPIRY_DAYS, validate_assignable_role
from booksphere.models.organization_invite import OrganizationInvite
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.repositories.invite_repository import InviteRepository
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.security.audit_logger import log_security_event
from booksphere.security.tokens import generate_opaque_token, hash_token
from booksphere.tasks.email_tasks import send_invite_email


class InviteService:
    def __init__(
        self,
        invite_repo: InviteRepository,
        membership_repo: MembershipRepository,
        user_repo: UserRepository,
    ) -> None:
        self._invites = invite_repo
        self._memberships = membership_repo
        self._users = user_repo

    def create_invite(
        self,
        organization_id: UUID,
        email: str,
        role: str,
        invited_by_user_id: UUID,
        organization_name: str,
        inviter_name: str,
        frontend_base_url: str,
    ) -> OrganizationInvite:
        validate_assignable_role(role)
        normalized_email = email.strip().lower()

        existing = self._invites.get_pending_for_org_and_email(organization_id, normalized_email)
        if existing is not None:
            raise DuplicatePendingInviteError(
                "There is already a pending invite for this email address."
            )

        raw_token = generate_opaque_token()
        invite = OrganizationInvite(
            organization_id=organization_id,
            email=normalized_email,
            role=role,
            invited_by_user_id=invited_by_user_id,
            token_hash=hash_token(raw_token),
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS),
        )
        self._invites.add(invite)
        self._invites.commit()

        accept_url = f"{frontend_base_url}/invites/{raw_token}"
        # Fire-and-forget: enqueues onto Celery, does NOT block this
        # request on email delivery. See email_tasks.py -- currently
        # logs instead of sending, per this feature's architecture
        # decision.
        send_invite_email.delay(
            to_email=normalized_email,
            organization_name=organization_name,
            inviter_name=inviter_name,
            accept_url=accept_url,
        )

        log_security_event(
            "invite_created",
            organization_id=str(organization_id),
            invited_email=normalized_email,
            role=role,
        )
        return invite

    def list_pending_invites(self, organization_id: UUID) -> list[OrganizationInvite]:
        return self._invites.list_pending_for_organization(organization_id)

    def revoke_invite(self, invite_id: UUID, organization_id: UUID) -> OrganizationInvite:
        invite = self._invites.get_for_organization(invite_id, organization_id)
        if invite is None:
            raise InviteNotFoundError()
        invite.status = "revoked"
        self._invites.commit()
        return invite

    def get_invite_by_token(self, raw_token: str) -> OrganizationInvite:
        """Used by the PUBLIC invite-preview endpoint (GET
        /invites/<token>) -- no auth required, the token itself is
        the credential. Callers must not leak WHY an invite is
        invalid beyond what's necessary (expired vs not-found are
        distinguished here because both are safe to reveal to
        whoever holds the token -- unlike, say, revealing whether an
        EMAIL exists, which login()/create_invite() deliberately
        never do)."""
        token_hash = hash_token(raw_token)
        invite = self._invites.get_by_token_hash(token_hash)
        if invite is None:
            raise InviteNotFoundError()
        if invite.status == "accepted":
            raise InviteAlreadyAcceptedError()
        if invite.status != "pending" or invite.expires_at < datetime.now(timezone.utc):
            raise InviteExpiredError()
        return invite

    def accept_invite(self, raw_token: str, accepting_user_id: UUID) -> OrganizationMembership:
        invite = self.get_invite_by_token(raw_token)

        accepting_user = self._users.get_by_id(accepting_user_id)

        # The invite was issued to a specific email address -- the
        # logged-in user accepting it must actually BE that person.
        # Without this check, User A could accept an invite meant for
        # User B simply by being logged in when they happen to click
        # the link, joining an organization they were never actually
        # invited to.
        if accepting_user is None or accepting_user.email != invite.email:
            raise InviteNotFoundError(
                "This invite was issued to a different email address."
            )

        existing_membership = self._memberships.get_for_user_and_org(
            accepting_user_id, invite.organization_id
        )
        if existing_membership is not None:
            # Already a member (e.g. re-clicking an old link) --
            # treat as a no-op success rather than an error, since
            # the end state the user wants (being a member) is
            # already true.
            invite.status = "accepted"
            invite.accepted_at = datetime.now(timezone.utc)
            self._invites.commit()
            return existing_membership

        membership = OrganizationMembership(
            user_id=accepting_user_id,
            organization_id=invite.organization_id,
            role=invite.role,
        )
        self._memberships.add(membership)

        invite.status = "accepted"
        invite.accepted_at = datetime.now(timezone.utc)
        self._invites.commit()

        log_security_event(
            "invite_accepted",
            organization_id=str(invite.organization_id),
            user_id=str(accepting_user_id),
            role=invite.role,
        )
        return membership
