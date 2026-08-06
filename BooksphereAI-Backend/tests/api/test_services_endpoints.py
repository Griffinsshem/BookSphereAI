from __future__ import annotations

from tests.api.test_resources_endpoints import (
    _add_membership,
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


class TestCreateServiceAuthorization:
    def test_owner_can_create_service(self, client, db_session):
        token, _ = _register_and_get_token(client, "svcowner@example.com", "Svc Org")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(token),
        )

        assert response.status_code == 201
        body = response.get_json()
        assert body["duration_minutes"] == 60
        assert body["currency"] == "USD"

    def test_customer_cannot_create_service(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "svcowner2@example.com", "Svc Org 2")
        org_id = _get_org_id_for_user(client, owner_token)

        customer_token, customer_id = _register_and_get_token(
            client, "customer@example.com", "Customer's Own Org"
        )
        _add_membership(customer_id, org_id, "customer")

        response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Should Fail", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(customer_token),
        )

        assert response.status_code == 403

    def test_rejects_invalid_duration(self, client, db_session):
        token, _ = _register_and_get_token(client, "svcowner3@example.com", "Svc Org 3")
        org_id = _get_org_id_for_user(client, token)

        response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Bad", "duration_minutes": 0, "price_cents": 8000},
            headers=_auth_headers(token),
        )

        assert response.status_code == 422


class TestLinkResourceAuthorization:
    def test_cannot_link_resource_from_different_organization(self, client, db_session):
        """End-to-end proof of the cross-tenant link defense, through
        the real HTTP API rather than just the service-layer unit
        test -- confirms the route correctly surfaces
        CrossTenantResourceLinkError as a 422, not a 500 or a silent
        success."""
        owner_a_token, _ = _register_and_get_token(client, "linkownerA@example.com", "Link Org A")
        org_a_id = _get_org_id_for_user(client, owner_a_token)
        service_response = client.post(
            f"/api/v1/organizations/{org_a_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(owner_a_token),
        )
        service_id = service_response.get_json()["id"]

        owner_b_token, _ = _register_and_get_token(client, "linkownerB@example.com", "Link Org B")
        org_b_id = _get_org_id_for_user(client, owner_b_token)
        resource_response = client.post(
            f"/api/v1/organizations/{org_b_id}/resources",
            json={"resource_type": "staff", "name": "Org B's Staff"},
            headers=_auth_headers(owner_b_token),
        )
        resource_id = resource_response.get_json()["id"]

        # Org A's owner attempts to link their service to Org B's
        # resource -- must be rejected.
        response = client.post(
            f"/api/v1/organizations/{org_a_id}/services/{service_id}/resources",
            json={"resource_id": resource_id},
            headers=_auth_headers(owner_a_token),
        )

        assert response.status_code == 422

    def test_can_link_resource_from_same_organization(self, client, db_session):
        token, _ = _register_and_get_token(client, "linkowner2@example.com", "Link Org 2")
        org_id = _get_org_id_for_user(client, token)

        service_response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(token),
        )
        service_id = service_response.get_json()["id"]

        resource_response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "staff", "name": "Masseuse"},
            headers=_auth_headers(token),
        )
        resource_id = resource_response.get_json()["id"]

        response = client.post(
            f"/api/v1/organizations/{org_id}/services/{service_id}/resources",
            json={"resource_id": resource_id},
            headers=_auth_headers(token),
        )

        assert response.status_code == 201


class TestServiceReadUpdateDelete:
    def test_get_service_detail(self, client, db_session):
        token, _ = _register_and_get_token(client, "svcread@example.com", "Svc Read Org")
        org_id = _get_org_id_for_user(client, token)
        create_response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(token),
        )
        service_id = create_response.get_json()["id"]

        response = client.get(
            f"/api/v1/organizations/{org_id}/services/{service_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        assert response.get_json()["name"] == "Massage"

    def test_get_service_cross_tenant_returns_404(self, client, db_session):
        owner_a_token, _ = _register_and_get_token(client, "svcA@example.com", "Svc Org A")
        org_a_id = _get_org_id_for_user(client, owner_a_token)
        create_response = client.post(
            f"/api/v1/organizations/{org_a_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(owner_a_token),
        )
        service_id = create_response.get_json()["id"]

        owner_b_token, _ = _register_and_get_token(client, "svcB@example.com", "Svc Org B")
        org_b_id = _get_org_id_for_user(client, owner_b_token)

        response = client.get(
            f"/api/v1/organizations/{org_b_id}/services/{service_id}",
            headers=_auth_headers(owner_b_token),
        )

        assert response.status_code == 404

    def test_update_service(self, client, db_session):
        token, _ = _register_and_get_token(client, "svcupdate@example.com", "Svc Update Org")
        org_id = _get_org_id_for_user(client, token)
        create_response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(token),
        )
        service_id = create_response.get_json()["id"]

        response = client.patch(
            f"/api/v1/organizations/{org_id}/services/{service_id}",
            json={"price_cents": 9000},
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        assert response.get_json()["price_cents"] == 9000

    def test_deactivate_service(self, client, db_session):
        token, _ = _register_and_get_token(client, "svcdeact@example.com", "Svc Deact Org")
        org_id = _get_org_id_for_user(client, token)
        create_response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Massage", "duration_minutes": 60, "price_cents": 8000},
            headers=_auth_headers(token),
        )
        service_id = create_response.get_json()["id"]

        response = client.delete(
            f"/api/v1/organizations/{org_id}/services/{service_id}",
            headers=_auth_headers(token),
        )

        assert response.status_code == 204

    def test_list_services_paginated(self, client, db_session):
        token, _ = _register_and_get_token(client, "svclist@example.com", "Svc List Org")
        org_id = _get_org_id_for_user(client, token)
        for i in range(3):
            client.post(
                f"/api/v1/organizations/{org_id}/services",
                json={"name": f"Service {i}", "duration_minutes": 30, "price_cents": 5000},
                headers=_auth_headers(token),
            )

        response = client.get(
            f"/api/v1/organizations/{org_id}/services", headers=_auth_headers(token)
        )

        assert response.status_code == 200
        assert response.get_json()["total"] == 3
