"""Organizations Blueprint -- currently just timezone management.
Deliberately minimal: full org settings (name change, logo, etc.) is
Team Management's territory, not this feature's. This exists only
because the timezone fix requires SOME way to set it after
registration."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.organizations.schemas import (
    OrganizationDetailSchema,
    UpdateOrganizationSchema,
)
from booksphere.domain.organizations.exceptions import (
    InvalidTimezoneError,
    OrganizationNotFoundError,
)
from booksphere.domain.organizations.value_objects import validate_timezone
from booksphere.extensions import db
from booksphere.middleware.tenant_context import require_organization_role
from booksphere.repositories.organization_repository import OrganizationRepository

organizations_bp = Blueprint(
    "organizations", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>"
)


@organizations_bp.route("", methods=["PATCH"])
@jwt_required()
def update_organization(organization_id):
    require_organization_role(organization_id, "owner")

    try:
        data = UpdateOrganizationSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    try:
        validate_timezone(data["timezone"])
    except InvalidTimezoneError as err:
        return jsonify({"error": {"code": "INVALID_TIMEZONE", "message": str(err)}}), 422

    org = OrganizationRepository().get_by_id(organization_id)
    if org is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Organization not found."}}), 404

    org.timezone = data["timezone"]
    db.session.commit()

    return jsonify(OrganizationDetailSchema().dump(org))
