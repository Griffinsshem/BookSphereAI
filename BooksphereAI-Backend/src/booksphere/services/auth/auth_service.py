"""
AuthService: registration, login, refresh, logout.

This is the ONLY place these operations are implemented. Routes call
this service and do nothing else — no queries, no password
verification, no token generation happen in the routes module. That
separation is what makes these operations testable without spinning up
Flask at all (see tests/unit/services/test_auth_service.py) and reusable
if we ever need to trigger registration from somewhere other than the
HTTP API (e.g. an admin CLI, a bulk-import job).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from flask_jwt_extended import create_access_token

from booksphere.domain.users.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    OrganizationSlugTakenError,
)
from booksphere.domain.users.value_objects import slugify
from booksphere.models.organization import Organization
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.models.refresh_token import RefreshToken
from booksphere.models.user import User
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.repositories.organization_repository import OrganizationRepository
from booksphere.repositories.refresh_token_repository import RefreshTokenRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.security.audit_logger import log_security_event
from booksphere.security.password_hasher import hash_password, verify_password
from booksphere.security.tokens import generate_opaque_token, hash_token


@dataclass(frozen=True)
class AuthTokens:
    """What the service hands back after login/refresh: an access
    token for the response body, and the RAW refresh token (only ever
    held in memory here — the route layer puts it in an httpOnly
    cookie and it is never returned in the JSON body)."""

    access_token: str
    raw_refresh_token: str
    csrf_token: str


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        membership_repo: MembershipRepository,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        self._users = user_repo
        self._orgs = org_repo
        self._memberships = membership_repo
        self._refresh_tokens = refresh_token_repo

    def register(
        self, email: str, password: str, full_name: str, organization_name: str
    ) -> tuple[User, Organization]:
        """Creates a User, a new Organization, and an 'owner'
        membership linking them, atomically."""
        normalized_email = email.strip().lower()

        if self._users.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError()

        slug = slugify(organization_name)
        if self._orgs.slug_exists(slug):
            slug = f"{slug}-{generate_opaque_token()[:6]}"

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
        )
        organization = Organization(name=organization_name, slug=slug)
        self._users.add(user)
        self._orgs.add(organization)

        from booksphere.extensions import db

        db.session.flush()

        membership = OrganizationMembership(
            user_id=user.id, organization_id=organization.id, role="owner"
        )
        self._memberships.add(membership)
        self._users.commit() 

        log_security_event(
            "user_registered", user_id=str(user.id), org_id=str(organization.id)
        )
        return user, organization

    def login(self, email: str, password: str) -> tuple[User, AuthTokens]:
        user = self._users.get_by_email(email.strip().lower())

        if user is None or not verify_password(password, user.password_hash):
            log_security_event("login_failed", email=email)
            raise InvalidCredentialsError()

        if not user.is_active:
            log_security_event("login_rejected_inactive", user_id=str(user.id))
            raise InvalidCredentialsError()

        tokens = self._issue_tokens(user.id)
        log_security_event("login_succeeded", user_id=str(user.id))
        return user, tokens

    def refresh(self, raw_refresh_token: str) -> AuthTokens:
        token_hash = hash_token(raw_refresh_token)
        existing = self._refresh_tokens.get_by_token_hash(token_hash)

        if existing is None or not existing.is_valid:
            log_security_event("refresh_rejected", token_hash=token_hash)
            raise InvalidRefreshTokenError()

        existing.revoked_at = datetime.now(timezone.utc)
        self._refresh_tokens.commit()

        return self._issue_tokens(existing.user_id)

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        existing = self._refresh_tokens.get_by_token_hash(token_hash)
        if existing is not None and existing.revoked_at is None:
            existing.revoked_at = datetime.now(timezone.utc)
            self._refresh_tokens.commit()
            log_security_event("logout", user_id=str(existing.user_id))

    def _issue_tokens(self, user_id: UUID) -> AuthTokens:
        access_token = create_access_token(identity=str(user_id))

        raw_refresh = generate_opaque_token()
        refresh_row = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        self._refresh_tokens.add(refresh_row)
        self._refresh_tokens.commit()

        csrf_token = generate_opaque_token()
        return AuthTokens(
            access_token=access_token,
            raw_refresh_token=raw_refresh,
            csrf_token=csrf_token,
        )
