"""
API tests for the Bookings endpoints: availability, creation
(including customer-vs-staff authorization split), listing (with
customer-scoped visibility), detail, and cancellation.
"""
from __future__ import annotations
from datetime import datetime, time, timedelta, timezone

from booksphere.extensions import db
from booksphere.models.organization_membership import OrganizationMembership
from booksphere.models.working_hours import WorkingHours
from tests.api.test_resources_endpoints import (
    _add_membership,
    _auth_headers,
    _get_org_id_for_user,
    _register_and_get_token,
)


def _next_occurrence_of_weekday(weekday: int, hour: int = 10) -> datetime:
    """Returns a datetime for the next occurrence of the given weekday
    (0=Monday..6=Sunday) at the given hour, at least 1 day from now --
    avoids "booking in the past" false failures depending on when the
    test suite happens to run."""
    now = datetime.now(timezone.utc) + timedelta(days=1)
    days_ahead = (weekday - now.weekday()) % 7
    target = now + timedelta(days=days_ahead)
    return target.replace(hour=hour, minute=0, second=0, microsecond=0)


def _setup_bookable_resource(client, owner_token, org_id):
    """Creates a resource with working hours covering EVERY day of
    the week, a service linked to it, returns both IDs. Covering
    every day deliberately -- these tests are about booking
    AUTHORIZATION (who can book for whom), not working-hours logic
    (already covered separately), so no test here should be coupled
    to which specific day "next Tuesday" etc. happens to be."""
    resource_response = client.post(
        f"/api/v1/organizations/{org_id}/resources",
        json={"resource_type": "room", "name": "Bookable Room"},
        headers=_auth_headers(owner_token),
    )
    resource_id = resource_response.get_json()["id"]

    for day in range(7):
        client.post(
            f"/api/v1/organizations/{org_id}/resources/{resource_id}/working-hours",
            json={"day_of_week": day, "start_time": "00:00:00", "end_time": "23:59:00"},
            headers=_auth_headers(owner_token),
        )

    service_response = client.post(
        f"/api/v1/organizations/{org_id}/services",
        json={"name": "Bookable Service", "duration_minutes": 60, "price_cents": 5000},
        headers=_auth_headers(owner_token),
    )
    service_id = service_response.get_json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/services/{service_id}/resources",
        json={"resource_id": resource_id},
        headers=_auth_headers(owner_token),
    )

    return resource_id, service_id


class TestAvailabilityEndpoint:
    def test_returns_available_slots(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "availowner@example.com", "Avail Org")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        target_date = _next_occurrence_of_weekday(0).date().isoformat()

        response = client.get(
            f"/api/v1/organizations/{org_id}/bookings/availability"
            f"?resource_id={resource_id}&service_id={service_id}&date={target_date}",
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 200
        assert len(response.get_json()["available_slots"]) > 0


class TestCreateBookingAuthorization:
    def test_customer_books_for_themselves(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner1@example.com", "Bk Org 1")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_token, customer_id = _register_and_get_token(
            client, "bkcustomer1@example.com", "Customer's Own Org"
        )
        _add_membership(customer_id, org_id, "customer")

        start_time = _next_occurrence_of_weekday(0).isoformat()

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={"resource_id": resource_id, "service_id": service_id, "start_time": start_time},
            headers=_auth_headers(customer_token),
        )

        assert response.status_code == 201
        assert response.get_json()["customer_id"] == customer_id

    def test_customer_cannot_book_for_someone_else(self, client, db_session):
        """Security-critical: a customer supplying a different
        customer_id must be IGNORED, not honored -- they can only ever
        book for themselves, per the earlier design decision."""
        owner_token, _ = _register_and_get_token(client, "bkowner2@example.com", "Bk Org 2")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_token, customer_id = _register_and_get_token(
            client, "bkcustomer2@example.com", "Customer2's Own Org"
        )
        _add_membership(customer_id, org_id, "customer")

        _, other_user_id = _register_and_get_token(client, "othervictim@example.com", "Victim Org")

        start_time = _next_occurrence_of_weekday(1).isoformat()

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": start_time,
                "customer_id": other_user_id,  # attempted impersonation
            },
            headers=_auth_headers(customer_token),
        )

        assert response.status_code == 201
        # Booked as the REQUESTER, not the impersonation attempt.
        assert response.get_json()["customer_id"] == customer_id

    def test_staff_can_book_on_behalf_of_a_customer(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner3@example.com", "Bk Org 3")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        staff_token, staff_id = _register_and_get_token(client, "bkstaff3@example.com", "Staff Org 3")
        _add_membership(staff_id, org_id, "staff")

        _, walkin_customer_id = _register_and_get_token(
            client, "walkin3@example.com", "Walkin Org"
        )
        _add_membership(walkin_customer_id, org_id, "customer")

        start_time = _next_occurrence_of_weekday(2).isoformat()

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": start_time,
                "customer_id": walkin_customer_id,
            },
            headers=_auth_headers(staff_token),
        )

        assert response.status_code == 201
        assert response.get_json()["customer_id"] == walkin_customer_id

    def test_rejects_resource_not_linked_to_service(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner4@example.com", "Bk Org 4")
        org_id = _get_org_id_for_user(client, owner_token)

        # Create a resource and service WITHOUT linking them.
        resource_response = client.post(
            f"/api/v1/organizations/{org_id}/resources",
            json={"resource_type": "room", "name": "Unlinked Room"},
            headers=_auth_headers(owner_token),
        )
        resource_id = resource_response.get_json()["id"]

        service_response = client.post(
            f"/api/v1/organizations/{org_id}/services",
            json={"name": "Unlinked Service", "duration_minutes": 60, "price_cents": 5000},
            headers=_auth_headers(owner_token),
        )
        service_id = service_response.get_json()["id"]

        start_time = _next_occurrence_of_weekday(0).isoformat()

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={"resource_id": resource_id, "service_id": service_id, "start_time": start_time},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "INVALID_RESOURCE_FOR_SERVICE"

    def test_rejects_booking_in_the_past(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner5@example.com", "Bk Org 5")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={"resource_id": resource_id, "service_id": service_id, "start_time": past_time},
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "BOOKING_IN_PAST"


class TestListBookingsAuthorization:
    def test_customer_sees_only_own_bookings(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner6@example.com", "Bk Org 6")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_a_token, customer_a_id = _register_and_get_token(
            client, "bkcustA@example.com", "Cust A Org"
        )
        _add_membership(customer_a_id, org_id, "customer")
        customer_b_token, customer_b_id = _register_and_get_token(
            client, "bkcustB@example.com", "Cust B Org"
        )
        _add_membership(customer_b_id, org_id, "customer")

        client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(0).isoformat(),
            },
            headers=_auth_headers(customer_a_token),
        )
        client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(1).isoformat(),
            },
            headers=_auth_headers(customer_b_token),
        )

        response = client.get(
            f"/api/v1/organizations/{org_id}/bookings", headers=_auth_headers(customer_a_token)
        )

        assert response.status_code == 200
        body = response.get_json()
        assert body["total"] == 1
        assert body["items"][0]["customer_id"] == customer_a_id

    def test_owner_sees_all_bookings(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner7@example.com", "Bk Org 7")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_token, customer_id = _register_and_get_token(
            client, "bkcust7@example.com", "Cust 7 Org"
        )
        _add_membership(customer_id, org_id, "customer")

        client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(0).isoformat(),
            },
            headers=_auth_headers(customer_token),
        )

        response = client.get(
            f"/api/v1/organizations/{org_id}/bookings", headers=_auth_headers(owner_token)
        )

        assert response.status_code == 200
        assert response.get_json()["total"] == 1


class TestBookingDetailAndCancel:
    def test_customer_cannot_view_someone_elses_booking(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner8@example.com", "Bk Org 8")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_a_token, customer_a_id = _register_and_get_token(
            client, "bkcustA8@example.com", "Cust A8 Org"
        )
        _add_membership(customer_a_id, org_id, "customer")
        customer_b_token, customer_b_id = _register_and_get_token(
            client, "bkcustB8@example.com", "Cust B8 Org"
        )
        _add_membership(customer_b_id, org_id, "customer")

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(0).isoformat(),
            },
            headers=_auth_headers(customer_a_token),
        )
        booking_id = create_response.get_json()["id"]

        response = client.get(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}",
            headers=_auth_headers(customer_b_token),
        )

        assert response.status_code == 404

    def test_customer_can_cancel_own_booking(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner9@example.com", "Bk Org 9")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        customer_token, customer_id = _register_and_get_token(
            client, "bkcust9@example.com", "Cust 9 Org"
        )
        _add_membership(customer_id, org_id, "customer")

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(0).isoformat(),
            },
            headers=_auth_headers(customer_token),
        )
        booking_id = create_response.get_json()["id"]

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            headers=_auth_headers(customer_token),
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "cancelled"

    def test_cancelling_frees_the_slot_for_a_new_booking(self, client, db_session):
        """End-to-end proof that cancellation actually works with the
        exclusion constraint's WHERE status='confirmed' filter: a
        cancelled booking must NOT continue blocking its old slot."""
        owner_token, _ = _register_and_get_token(client, "bkowner10@example.com", "Bk Org 10")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        start_time = _next_occurrence_of_weekday(0).isoformat()

        first = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={"resource_id": resource_id, "service_id": service_id, "start_time": start_time},
            headers=_auth_headers(owner_token),
        )
        booking_id = first.get_json()["id"]

        client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            headers=_auth_headers(owner_token),
        )

        second = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={"resource_id": resource_id, "service_id": service_id, "start_time": start_time},
            headers=_auth_headers(owner_token),
        )

        assert second.status_code == 201

    def test_cannot_cancel_already_cancelled_booking(self, client, db_session):
        owner_token, _ = _register_and_get_token(client, "bkowner11@example.com", "Bk Org 11")
        org_id = _get_org_id_for_user(client, owner_token)
        resource_id, service_id = _setup_bookable_resource(client, owner_token, org_id)

        create_response = client.post(
            f"/api/v1/organizations/{org_id}/bookings",
            json={
                "resource_id": resource_id,
                "service_id": service_id,
                "start_time": _next_occurrence_of_weekday(0).isoformat(),
            },
            headers=_auth_headers(owner_token),
        )
        booking_id = create_response.get_json()["id"]

        client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            headers=_auth_headers(owner_token),
        )

        response = client.post(
            f"/api/v1/organizations/{org_id}/bookings/{booking_id}/cancel",
            headers=_auth_headers(owner_token),
        )

        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "ALREADY_CANCELLED"
