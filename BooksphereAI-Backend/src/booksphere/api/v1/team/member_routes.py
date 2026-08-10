from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.team.schemas import ChangeRoleSchema, MemberResponseSchema
from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    InvalidRoleError,
    LastOwnerProtectionError,
    MembershipNotFoundError,
)
from booksphere.middleware.tenant_context import require_organization_role
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.services.team.membership_service import MembershipService

members_bp = Blueprint(
    "members", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>/members"
)


def _build_service() -> MembershipService:
    return MembershipService(MembershipRepository())


@members_bp.route("", methods=["GET"])
@jwt_required()
def list_members(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")
    service = _build_service()
    members = service.list_members(organization_id)
    return jsonify(MemberResponseSchema(many=True).dump(members))


@members_bp.route("/<uuid:user_id>", methods=["PATCH"])
@jwt_required()
def change_member_role(organization_id, user_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = ChangeRoleSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        membership = service.change_role(organization_id, user_id, data["role"])
    except MembershipNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Member not found."}}), 404
    except CannotModifyOwnerRoleError as err:
        return jsonify({"error": {"code": "CANNOT_MODIFY_OWNER", "message": str(err)}}), 422
    except InvalidRoleError as err:
        return jsonify({"error": {"code": "INVALID_ROLE", "message": str(err)}}), 422

    return jsonify(MemberResponseSchema().dump(membership))


@members_bp.route("/<uuid:user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(organization_id, user_id):
    require_organization_role(organization_id, "owner", "manager")

    service = _build_service()
    try:
        service.remove_member(organization_id, user_id)
    except MembershipNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Member not found."}}), 404
    except CannotModifyOwnerRoleError as err:
        return jsonify({"error": {"code": "CANNOT_MODIFY_OWNER", "message": str(err)}}), 422
    except LastOwnerProtectionError as err:
        return jsonify({"error": {"code": "LAST_OWNER", "message": str(err)}}), 422

    return "", 204
