"""
API tests for the invite lifecycle: create -> list -> preview ->
accept -> membership actually created. Plus the authorization checks
specific to invites (owner/manager only can create/list/revoke).
"""
from __future__ import annotations

from tests.api.test_resources_endpoints import (
    _add_membership,
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


class TestCreateInvite:
    def test_owner_can_create_invite(self, client, db_session):
        token, _ = _register_and_get_token(client, "invowner@example.com", "Invite Org")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "invitee@example.com", "role": "staff"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 201
        assert response.get_json()["email"] == "invitee@example.com"
        assert response.get_json()["status"] == "pending"

    def test_staff_cannot_create_invite(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "invowner2@example.com", "Invite Org 2")
        org_id = _get_org_id_for_user(client, owner_token)
        staff_token, staff_id = _register_and_get_token(client, "invstaff2@example.com", "Staff Org")
        _add_membership(staff_id, org_id, "staff")

        response = client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "someone@example.com", "role": "staff"},
            headers=_auth_headers(staff_token),
        )

        assert response.status_code == 403

    def test_cannot_invite_as_owner(self, client, db_session):
        token, _ = _register_and_get_token(client, "invowner3@example.com", "Invite Org 3")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "wouldbeowner@example.com", "role": "owner"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "CANNOT_INVITE_AS_OWNER"

    def test_duplicate_pending_invite_rejected(self, client, db_session):
        token, _ = _register_and_get_token(client, "invowner4@example.com", "Invite Org 4")
        org_id = _get_org_id_for_user(client, token)
        payload = {"email": "dup@example.com", "role": "staff"}

        client.post(
            f"/api/v1/organizations/{org_id}/invites", json=payload, headers=_auth_headers(token)
        )
        response = client.post(
            f"/api/v1/organizations/{org_id}/invites", json=payload, headers=_auth_headers(token)
        )

        assert response.status_code == 409


class TestListAndRevokeInvites:
    def test_owner_can_list_pending_invites(self, client, db_session):
        token, _ = _register_and_get_token(client, "invowner5@example.com", "Invite Org 5")
        org_id = _get_org_id_for_user(client, token)
        client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "listed@example.com", "role": "staff"},
            headers=_auth_headers(token),
        )

        response = client.get(
            f"/api/v1/organizations/{org_id}/invites", headers=_auth_headers(token)
        )

        assert response.status_code == 200
        assert len(response.get_json()) == 1

    def test_owner_can_revoke_invite(self, client, db_session):
        token, _ = _register_and_get_token(client, "invowner6@example.com", "Invite Org 6")
        org_id = _get_org_id_for_user(client, token)
        create_response = client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "torevoke@example.com", "role": "staff"},
            headers=_auth_headers(token),
        )
        invite_id = create_response.get_json()["id"]

        response = client.delete(
            f"/api/v1/organizations/{org_id}/invites/{invite_id}", headers=_auth_headers(token)
        )
        assert response.status_code == 204

        list_response = client.get(
            f"/api/v1/organizations/{org_id}/invites", headers=_auth_headers(token)
        )
        assert len(list_response.get_json()) == 0


class TestInvitePreviewAndAccept:
    def test_full_invite_and_accept_flow(self, client, db_session):
        """End-to-end: create invite -> the invitee registers their
        OWN account (with the SAME email the invite was sent to) ->
        previews the invite -> accepts it -> is now a real member."""
        owner_token, _ = _register_and_get_token(client, "flowowner@example.com", "Flow Org")
        org_id = _get_org_id_for_user(client, owner_token)

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "invitee-flow@example.com", "role": "manager"},
            headers=_auth_headers(owner_token),
        )
        assert create_response.status_code == 201

        # We don't have the raw token from the API response (by
        # design -- it's never returned, only logged via the Celery
        # task). For this test, fetch it directly from the DB.
        from booksphere.models.organization_invite import OrganizationInvite

        invite_row = OrganizationInvite.query.filter_by(email="invitee-flow@example.com").first()
        assert invite_row is not None

        # We can't reverse the hash, so directly exercise the
        # accept-by-token endpoint using the SERVICE layer's own
        # hashing to construct a token the API can verify -- simplest
        # is to monkeypatch isn't available at this level, so instead
        # we register the invitee, then call accept_invite via a
        # freshly minted raw token whose hash we insert directly.
        import uuid as uuid_module
        from booksphere.security.tokens import generate_opaque_token, hash_token
        from booksphere.extensions import db

        raw_token = generate_opaque_token()
        invite_row.token_hash = hash_token(raw_token)
        db.session.commit()

        invitee_token, invitee_id = _register_and_get_token(
            client, "invitee-flow@example.com", "Invitee's Own Org"
        )

        preview_response = client.get(f"/api/v1/invites/{raw_token}")
        assert preview_response.status_code == 200
        assert preview_response.get_json()["organization_name"] == "Flow Org"
        assert preview_response.get_json()["role"] == "manager"

        accept_response = client.post(
            f"/api/v1/invites/{raw_token}/accept", headers=_auth_headers(invitee_token)
        )
        assert accept_response.status_code == 200
        assert accept_response.get_json()["role"] == "manager"

        members_response = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=_auth_headers(owner_token)
        )
        emails = [m["email"] for m in members_response.get_json()]
        assert "invitee-flow@example.com" in emails

    def test_accept_rejects_wrong_email(self, client, db_session):
        """SECURITY-CRITICAL: an invite issued to email A cannot be
        accepted by a logged-in user with a DIFFERENT email, even
        with a valid, unexpired token."""
        owner_token, _ = _register_and_get_token(client, "wrongowner@example.com", "Wrong Org")
        org_id = _get_org_id_for_user(client, owner_token)

        client.post(
            f"/api/v1/organizations/{org_id}/invites",
            json={"email": "intended@example.com", "role": "staff"},
            headers=_auth_headers(owner_token),
        )

        from booksphere.models.organization_invite import OrganizationInvite
        from booksphere.security.tokens import generate_opaque_token, hash_token
        from booksphere.extensions import db

        invite_row = OrganizationInvite.query.filter_by(email="intended@example.com").first()
        raw_token = generate_opaque_token()
        invite_row.token_hash = hash_token(raw_token)
        db.session.commit()

        wrong_person_token, _ = _register_and_get_token(
            client, "totally-different@example.com", "Different Org"
        )

        response = client.post(
            f"/api/v1/invites/{raw_token}/accept", headers=_auth_headers(wrong_person_token)
        )
        assert response.status_code == 404
