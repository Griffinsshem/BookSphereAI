"""
API tests for member management: list, change role, remove.
Authorization matrix: owner AND manager can both change
roles/remove members; staff/customer cannot; NEITHER owner nor
manager can touch the owner's own role/membership.
"""
from __future__ import annotations

from tests.api.test_resources_endpoints import (
    _add_membership,
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


class TestListMembers:
    def test_any_member_can_list(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner1@example.com", "Mem Org 1")
        org_id = _get_org_id_for_user(client, owner_token)
        _, staff_id = _register_and_get_token(client, "memstaff1@example.com", "Staff Org 1")
        _add_membership(staff_id, org_id, "staff")

        response = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=_auth_headers(owner_token)
        )

        assert response.status_code == 200
        assert len(response.get_json()) == 2
        # Owner sorted first, per list_for_organization_ordered.
        assert response.get_json()[0]["role"] == "owner"


class TestChangeRole:
    def test_owner_can_promote_staff_to_manager(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner2@example.com", "Mem Org 2")
        org_id = _get_org_id_for_user(client, owner_token)
        _, staff_id = _register_and_get_token(client, "memstaff2@example.com", "Staff Org 2")
        _add_membership(staff_id, org_id, "staff")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{staff_id}",
            json={"role": "manager"},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 200
        assert response.get_json()["role"] == "manager"

    def test_manager_can_also_promote_staff(self, client, db_session):
        """Confirms the DELEGATION half of the architecture decision:
        managers, not just owners, can perform routine role changes."""
        owner_token, _ = _register_and_get_token(client, "memowner3@example.com", "Mem Org 3")
        org_id = _get_org_id_for_user(client, owner_token)
        manager_token, manager_id = _register_and_get_token(
            client, "memmanager3@example.com", "Manager Org 3"
        )
        _add_membership(manager_id, org_id, "manager")
        _, staff_id = _register_and_get_token(client, "memstaff3@example.com", "Staff Org 3")
        _add_membership(staff_id, org_id, "staff")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{staff_id}",
            json={"role": "customer"},
            headers=_auth_headers(manager_token),
        )

        assert response.status_code == 200
        assert response.get_json()["role"] == "customer"

    def test_staff_cannot_change_roles(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner4@example.com", "Mem Org 4")
        org_id = _get_org_id_for_user(client, owner_token)
        staff_token, staff_id = _register_and_get_token(client, "memstaff4@example.com", "Staff Org 4")
        _add_membership(staff_id, org_id, "staff")
        _, other_id = _register_and_get_token(client, "memother4@example.com", "Other Org 4")
        _add_membership(other_id, org_id, "customer")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{other_id}",
            json={"role": "manager"},
            headers=_auth_headers(staff_token),
        )

        assert response.status_code == 403

    def test_manager_cannot_change_the_owners_role(self, client, db_session):
        """SECURITY-CRITICAL, end-to-end through the real HTTP API:
        a manager (an elevated, trusted role) still cannot touch the
        owner's role -- proving the protection isn't just "requires
        owner permission" (which a manager might satisfy via a bug)
        but a genuinely separate, unconditional guard."""
        owner_token, owner_id = _register_and_get_token(
            client, "memowner5@example.com", "Mem Org 5"
        )
        org_id = _get_org_id_for_user(client, owner_token)
        manager_token, manager_id = _register_and_get_token(
            client, "memmanager5@example.com", "Manager Org 5"
        )
        _add_membership(manager_id, org_id, "manager")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{owner_id}",
            json={"role": "staff"},
            headers=_auth_headers(manager_token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "CANNOT_MODIFY_OWNER"

    def test_cannot_grant_owner_role_via_api(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner6@example.com", "Mem Org 6")
        org_id = _get_org_id_for_user(client, owner_token)
        _, staff_id = _register_and_get_token(client, "memstaff6@example.com", "Staff Org 6")
        _add_membership(staff_id, org_id, "staff")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{staff_id}",
            json={"role": "owner"},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "CANNOT_MODIFY_OWNER"


class TestRemoveMember:
    def test_owner_can_remove_a_staff_member(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner7@example.com", "Mem Org 7")
        org_id = _get_org_id_for_user(client, owner_token)
        _, staff_id = _register_and_get_token(client, "memstaff7@example.com", "Staff Org 7")
        _add_membership(staff_id, org_id, "staff")

        response = client.delete(
            f"/api/v1/organizations/{org_id}/members/{staff_id}", headers=_auth_headers(owner_token)
        )

        assert response.status_code == 204

    def test_cannot_remove_the_owner(self, client, db_session):
        owner_token, owner_id = _register_and_get_token(
            client, "memowner8@example.com", "Mem Org 8"
        )
        org_id = _get_org_id_for_user(client, owner_token)

        response = client.delete(
            f"/api/v1/organizations/{org_id}/members/{owner_id}", headers=_auth_headers(owner_token)
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "CANNOT_MODIFY_OWNER"

    def test_non_member_cannot_remove_anyone(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "memowner9@example.com", "Mem Org 9")
        org_id = _get_org_id_for_user(client, owner_token)
        _, staff_id = _register_and_get_token(client, "memstaff9@example.com", "Staff Org 9")
        _add_membership(staff_id, org_id, "staff")
        outsider_token, _ = _register_and_get_token(client, "outsider9@example.com", "Outsider Org")

        response = client.delete(
            f"/api/v1/organizations/{org_id}/members/{staff_id}",
            headers=_auth_headers(outsider_token),
        )

        assert response.status_code == 403
