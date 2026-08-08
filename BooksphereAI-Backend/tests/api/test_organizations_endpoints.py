from __future__ import annotations

from tests.api.test_resources_endpoints import (
    _add_membership,
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


class TestUpdateOrganizationTimezone:
    def test_owner_can_set_timezone(self, client, db_session):
        token, _ = _register_and_get_token(client, "tzowner@example.com", "TZ Org")
        org_id = _get_org_id_for_user(client, token)

        response = client.patch(
            f"/api/v1/organizations/{org_id}",
            json={"timezone": "Africa/Nairobi"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        assert response.get_json()["timezone"] == "Africa/Nairobi"

    def test_rejects_invalid_timezone(self, client, db_session):
        token, _ = _register_and_get_token(client, "tzowner2@example.com", "TZ Org 2")
        org_id = _get_org_id_for_user(client, token)

        response = client.patch(
            f"/api/v1/organizations/{org_id}",
            json={"timezone": "Not/A/Real/Zone"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "INVALID_TIMEZONE"

    def test_staff_cannot_set_timezone(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "tzowner3@example.com", "TZ Org 3")
        org_id = _get_org_id_for_user(client, owner_token)

        staff_token, staff_id = _register_and_get_token(client, "tzstaff3@example.com", "Staff Org")
        _add_membership(staff_id, org_id, "staff")

        response = client.patch(
            f"/api/v1/organizations/{org_id}",
            json={"timezone": "Africa/Nairobi"},
            headers=_auth_headers(staff_token),
        )

        assert response.status_code == 403
