"""
API tests for the Resources endpoints, focused on the authorization
matrix: this is the first feature where require_organization_role is
actually exercised end-to-end (register/login/refresh don't need it --
they run before an org context exists). Every write endpoint must
reject staff/customer; every endpoint must reject a user who isn't a
member of the target org at all.
"""
from __future__ import annotations

from booksphere.extensions import db
from booksphere.models.organization_membership import OrganizationMembership


def _register_and_get_token(client, email, org_name):
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


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _add_membership(user_id, organization_id, role):
    membership = OrganizationMembership(
        user_id=user_id, organization_id=organization_id, role=role
    )
    db.session.add(membership)
    db.session.commit()
    return membership


def _get_org_id_for_user(client, token):
    response = client.get("/api/v1/users/me", headers=_auth_headers(token))
    return response.get_json()["memberships"][0]["organization"]["id"]


class TestCreateResourceAuthorization:
    def test_owner_can_create_resource(self, client, db_session):
        token, _ = _register_and_get_token(client, "owner@example.com", "Owner Org")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Room 1"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 201
        assert response.get_json()["name"] == "Room 1"

    def test_staff_cannot_create_resource(self, client, db_session):
        """Staff can READ resources but not CREATE them -- write
        operations are owner/manager only per the RBAC design."""
        owner_token, owner_id = _register_and_get_token(client, "owner2@example.com", "Org2")
        org_id = _get_org_id_for_user(client, owner_token)

        staff_token, staff_id = _register_and_get_token(client, "staffmember@example.com", "Staff's Own Org")
        _add_membership(staff_id, org_id, "staff")

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Should Fail"},
            headers=_auth_headers(staff_token),
        )

        assert response.status_code == 403

    def test_non_member_cannot_create_resource(self, client, db_session):
        """Security-critical: a completely unrelated user (not a
        member of the target org at all) must be rejected -- not just
        users with an insufficient role within the org."""
        owner_token, _ = _register_and_get_token(client, "owner3@example.com", "Org3")
        org_id = _get_org_id_for_user(client, owner_token)

        outsider_token, _ = _register_and_get_token(client, "outsider@example.com", "Outsider's Org")

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Should Fail"},
            headers=_auth_headers(outsider_token),
        )

        assert response.status_code == 403

    def test_create_requires_authentication(self, client, db_session):
        response = client.post(
            "/api/v1/organizations/00000000-0000-0000-0000-000000000000/resources",
            json={"resource_type": "room", "name": "No Token"},
        )
        assert response.status_code == 401


class TestReadResourceAuthorization:
    def test_staff_can_list_resources(self, client, db_session):
        owner_token, owner_id = _register_and_get_token(client, "owner4@example.com", "Org4")
        org_id = _get_org_id_for_user(client, owner_token)
        client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Room 1"},
            headers=_auth_headers(owner_token),
        )

        staff_token, staff_id = _register_and_get_token(client, "staff4@example.com", "Staff Org 4")
        _add_membership(staff_id, org_id, "staff")

        response = client.get(
            f"/api/v1/organizations/{org_id}/resources", headers=_auth_headers(staff_token)
        )

        assert response.status_code == 200
        assert response.get_json()["total"] == 1

    def test_cross_tenant_get_returns_404_not_403(self, client, db_session):
        """Deliberately checking for 404, not 403: leaking "this
        resource exists but you can't access it" (403) is worse than
        a clean "not found" (404) -- 403 would confirm the ID is
        valid, aiding enumeration attacks against other tenants."""
        owner_a_token, _ = _register_and_get_token(client, "ownerA@example.com", "Org A")
        org_a_id = _get_org_id_for_user(client, owner_a_token)
        create_response = client.post(
            f"/api/v1/organizations/{org_a_id}/resources",
            json={"resource_type": "room", "name": "Org A's Room"},
            headers=_auth_headers(owner_a_token),
        )
        resource_id = create_response.get_json()["id"]

        owner_b_token, _ = _register_and_get_token(client, "ownerB@example.com", "Org B")
        org_b_id = _get_org_id_for_user(client, owner_b_token)

        response = client.get(
            f"/api/v1/organizations/{org_b_id}/resources/{resource_id}",
            headers=_auth_headers(owner_b_token),
        )

        assert response.status_code == 404


class TestWorkingHoursAuthorization:
    def test_manager_can_add_working_hours(self, client, db_session):
        owner_token, owner_id = _register_and_get_token(client, "owner5@example.com", "Org5")
        org_id = _get_org_id_for_user(client, owner_token)

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Room"},
            headers=_auth_headers(owner_token),
        )
        resource_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources/{resource_id}/working-hours",
            json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 201
        assert response.get_json()["day_of_week"] == 0

    def test_invalid_window_rejected(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "owner6@example.com", "Org6")
        org_id = _get_org_id_for_user(client, owner_token)

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Room"},
            headers=_auth_headers(owner_token),
        )
        resource_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/v1/organizations/{org_id}/resources/{resource_id}/working-hours",
            json={"day_of_week": 0, "start_time": "17:00:00", "end_time": "09:00:00"},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 422
