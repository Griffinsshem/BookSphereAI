"""
Bookings Blueprint.

Authorization here is finer-grained than require_organization_role
alone provides: a customer can only create/view/cancel THEIR OWN
bookings, while staff/manager/owner can act on any booking in the
org. This is "own resource, or elevated role" -- a pattern this
feature introduces that require_organization_role (all-or-nothing by
role) doesn't cover on its own, so routes combine it with an explicit
ownership check.
"""
from __future__ import annotations
from datetime import date as date_type

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from werkzeug.exceptions import Forbidden

from booksphere.api.v1.bookings.schemas import (
    AvailabilityQuerySchema,
    BookingResponseSchema,
    CreateBookingSchema,
)
from booksphere.domain.bookings.exceptions import (
    BookingAlreadyCancelledError,
    BookingInThePastError,
    BookingNotFoundError,
    OutsideWorkingHoursError,
    ResourceNotLinkedToServiceError,
    SlotUnavailableError,
)
from booksphere.domain.resources.exceptions import ResourceNotFoundError, ServiceNotFoundError
from booksphere.middleware.tenant_context import get_membership_role, require_organization_role
from booksphere.repositories.booking_repository import BookingRepository
from booksphere.repositories.organization_repository import OrganizationRepository
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.service_repository import ServiceRepository
from booksphere.repositories.service_resource_repository import ServiceResourceRepository
from booksphere.repositories.working_hours_repository import WorkingHoursRepository
from booksphere.services.bookings.booking_service import BookingService

bookings_bp = Blueprint(
    "bookings", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>/bookings"
)

_STAFF_AND_ABOVE = ("owner", "manager", "staff")


def _build_service() -> BookingService:
    return BookingService(
        BookingRepository(),
        ResourceRepository(),
        ServiceRepository(),
        ServiceResourceRepository(),
        WorkingHoursRepository(),
        OrganizationRepository(),
    )


@bookings_bp.route("/availability", methods=["GET"])
@jwt_required()
def get_availability(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    try:
        params = AvailabilityQuerySchema().load(request.args)
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        slots = service.get_availability(
            organization_id, params["resource_id"], params["service_id"], params["date"]
        )
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404

    return jsonify({"available_slots": [slot.isoformat() for slot in slots]})


@bookings_bp.route("", methods=["POST"])
@jwt_required()
def create_booking(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    try:
        data = CreateBookingSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    requester_id = get_jwt_identity()
    role = get_membership_role(organization_id)

    if role in _STAFF_AND_ABOVE and data.get("customer_id"):
        # Staff/manager/owner may book on behalf of a specific
        # customer, per the earlier design decision.
        customer_id = data["customer_id"]
    else:
        # A plain customer (or anyone who didn't supply customer_id)
        # can ONLY ever book for themselves -- this is enforced here,
        # server-side, regardless of what a client sends. A customer
        # cannot impersonate another customer by passing a different
        # customer_id; that value is simply ignored for their role.
        customer_id = requester_id

    service = _build_service()
    try:
        booking = service.create_booking(
            organization_id=organization_id,
            resource_id=data["resource_id"],
            service_id=data["service_id"],
            customer_id=customer_id,
            start_time=data["start_time"],
            notes=data.get("notes"),
        )
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404
    except ResourceNotLinkedToServiceError as err:
        return jsonify({"error": {"code": "INVALID_RESOURCE_FOR_SERVICE", "message": str(err)}}), 422
    except BookingInThePastError as err:
        return jsonify({"error": {"code": "BOOKING_IN_PAST", "message": str(err)}}), 422
    except OutsideWorkingHoursError as err:
        return jsonify({"error": {"code": "OUTSIDE_WORKING_HOURS", "message": str(err)}}), 422
    except SlotUnavailableError as err:
        return jsonify({"error": {"code": "SLOT_UNAVAILABLE", "message": str(err)}}), 409

    return jsonify(BookingResponseSchema().dump(booking)), 201


@bookings_bp.route("", methods=["GET"])
@jwt_required()
def list_bookings(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    requester_id = get_jwt_identity()
    role = get_membership_role(organization_id)
    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)

    # Customers see only their own bookings; staff and above see all
    # -- enforced by conditionally passing customer_id into the
    # repository query itself, not by filtering results in Python
    # after the fact (which would be easy to get wrong or forget).
    customer_filter = None if role in _STAFF_AND_ABOVE else requester_id

    repo = BookingRepository()
    pagination = repo.list_for_organization(
        organization_id, customer_id=customer_filter, page=page, per_page=per_page
    )

    return jsonify(
        {
            "items": BookingResponseSchema(many=True).dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    )


@bookings_bp.route("/<uuid:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(organization_id, booking_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    requester_id = get_jwt_identity()
    role = get_membership_role(organization_id)

    service = _build_service()
    try:
        booking = service.get_booking(booking_id, organization_id)
    except BookingNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Booking not found."}}), 404

    if role not in _STAFF_AND_ABOVE and str(booking.customer_id) != str(requester_id):
        # A customer trying to view someone ELSE's booking -- 404, not
        # 403, matching our established IDOR-safe pattern: don't
        # confirm the booking exists to someone who shouldn't see it.
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Booking not found."}}), 404

    return jsonify(BookingResponseSchema().dump(booking))


@bookings_bp.route("/<uuid:booking_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_booking(organization_id, booking_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    requester_id = get_jwt_identity()
    role = get_membership_role(organization_id)

    service = _build_service()
    try:
        booking = service.get_booking(booking_id, organization_id)
    except BookingNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Booking not found."}}), 404

    if role not in _STAFF_AND_ABOVE and str(booking.customer_id) != str(requester_id):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Booking not found."}}), 404

    try:
        cancelled = service.cancel_booking(booking_id, organization_id)
    except BookingAlreadyCancelledError:
        return jsonify({"error": {"code": "ALREADY_CANCELLED", "message": "This booking is already cancelled."}}), 422

    return jsonify(BookingResponseSchema().dump(cancelled))
