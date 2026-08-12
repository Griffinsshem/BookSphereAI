"""
API tests for email verification: the gate blocking unverified users
from create-booking/create-invite/create-resource, and the full
register -> verify -> retry sequence succeeding afterward.
"""
from __future__ import annotations

from booksphere.extensions import db
from booksphere.models.email_verification_token import EmailVerificationToken
from booksphere.security.tokens import generate_opaque_token, hash_token
from tests.api.test_resources_endpoints import (
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


def _register_unverified(client, email, org_name):
    """Registers a user WITHOUT auto-verifying -- deliberately
    bypasses the shared _register_and_get_token helper (imported
    above), which auto-verifies by design so every OTHER test file in
    the project doesn't need to route through the verify flow just to
    perform ordinary write actions. This file specifically needs the
    genuinely-unverified state to test the gate itself."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple-1",
            "full_name": "Test User",
            "organization_name": org_name,
        },
    )
    body = response.get_json()
    return body["access_token"], body["user"]["id"]


def _get_raw_verification_token(email: str) -> str:
    """Test helper: since the real token is never returned by the API
    (only its hash is stored, matching the invite pattern), directly
    overwrite the stored hash with a known raw value for testing --
    same technique used for invite tests in Team Management."""
    from booksphere.models.user import User

    user = User.query.filter_by(email=email).first()
    token_row = (
        EmailVerificationToken.query.filter_by(user_id=user.id)
        .order_by(EmailVerificationToken.created_at.desc())
        .first()
    )
    raw_token = generate_opaque_token()
    token_row.token_hash = hash_token(raw_token)
    db.session.commit()
    return raw_token


class TestEmailVerificationGate:
    def test_unverified_user_cannot_create_resource(self, client, db_session):
        token, _ = _register_unverified(client, "gateowner@example.com", "Gate Org")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Should Be Blocked"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

    def test_verified_user_can_create_resource(self, client, db_session):
        token, _ = _register_and_get_token(client, "verifiedowner@example.com", "Verified Org")
        org_id = _get_org_id_for_user(client, token)

        raw_token = _get_raw_verification_token("verifiedowner@example.com")
        client.post(f"/api/v1/auth/verify-email/{raw_token}")

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Should Succeed"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 201

    def test_users_me_reports_verification_status(self, client, db_session):
        token, _ = _register_unverified(client, "mecheck@example.com", "Me Check Org")

        response = client.get("/api/v1/users/me", headers=_auth_headers(token))

        assert response.get_json()["user"]["email_verified"] is False


class TestVerifyEmailEndpoint:
    def test_confirms_a_valid_token(self, client, db_session):
        _register_and_get_token(client, "confirmflow@example.com", "Confirm Org")
        raw_token = _get_raw_verification_token("confirmflow@example.com")

        response = client.post(f"/api/v1/auth/verify-email/{raw_token}")

        assert response.status_code == 200

    def test_rejects_unknown_token(self, client, db_session):
        response = client.post("/api/v1/auth/verify-email/not-a-real-token")
        assert response.status_code == 404

    def test_rejects_reusing_an_already_confirmed_token(self, client, db_session):
        _register_and_get_token(client, "reuseflow@example.com", "Reuse Org")
        raw_token = _get_raw_verification_token("reuseflow@example.com")

        first = client.post(f"/api/v1/auth/verify-email/{raw_token}")
        assert first.status_code == 200

        second = client.post(f"/api/v1/auth/verify-email/{raw_token}")
        assert second.status_code == 410


class TestResendVerification:
    def test_resend_issues_a_new_email(self, client, db_session):
        token, _ = _register_unverified(client, "resendflow@example.com", "Resend Org")

        response = client.post("/api/v1/auth/resend-verification", headers=_auth_headers(token))

        assert response.status_code == 200

    def test_resend_rejected_if_already_verified(self, client, db_session):
        token, _ = _register_and_get_token(client, "alreadyverified@example.com", "AV Org")
        raw_token = _get_raw_verification_token("alreadyverified@example.com")
        client.post(f"/api/v1/auth/verify-email/{raw_token}")

        response = client.post("/api/v1/auth/resend-verification", headers=_auth_headers(token))

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "ALREADY_VERIFIED"
