"""
Invite Blueprint. Two distinct auth postures on purpose:
  - /organizations/<org_id>/invites/* requires org membership
    (owner/manager) -- managing an org's outbound invites.
  - /invites/<token>/* requires only being LOGGED IN (any user) --
    the invite token itself is the authorization to view/accept it,
    not org membership (the whole point is the invitee ISN'T a
    member yet).
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.team.schemas import (
    CreateInviteSchema,
    InvitePreviewSchema,
    InviteResponseSchema,
)
from booksphere.domain.team.exceptions import (
    CannotModifyOwnerRoleError,
    DuplicatePendingInviteError,
    InvalidRoleError,
    InviteAlreadyAcceptedError,
    InviteExpiredError,
    InviteNotFoundError,
)
from booksphere.middleware.tenant_context import require_organization_role
from booksphere.repositories.invite_repository import InviteRepository
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.repositories.organization_repository import OrganizationRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.services.team.invite_service import InviteService

org_invites_bp = Blueprint(
    "org_invites", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>/invites"
)
invites_bp = Blueprint("invites", __name__, url_prefix="/api/v1/invites")


def _build_service() -> InviteService:
    return InviteService(InviteRepository(), MembershipRepository(), UserRepository())


@org_invites_bp.route("", methods=["POST"])
@jwt_required()
def create_invite(organization_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = CreateInviteSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    inviter_id = get_jwt_identity()
    inviter = UserRepository().get_by_id(inviter_id)
    org = OrganizationRepository().get_by_id(organization_id)

    frontend_base_url = request.headers.get("Origin") or "http://localhost:3000"

    service = _build_service()
    try:
        invite = service.create_invite(
            organization_id=organization_id,
            email=data["email"],
            role=data["role"],
            invited_by_user_id=inviter_id,
            organization_name=org.name if org else "",
            inviter_name=inviter.full_name if inviter else "",
            frontend_base_url=frontend_base_url,
        )
    except CannotModifyOwnerRoleError as err:
        return jsonify({"error": {"code": "CANNOT_INVITE_AS_OWNER", "message": str(err)}}), 422
    except InvalidRoleError as err:
        return jsonify({"error": {"code": "INVALID_ROLE", "message": str(err)}}), 422
    except DuplicatePendingInviteError as err:
        return jsonify({"error": {"code": "DUPLICATE_INVITE", "message": str(err)}}), 409

    return jsonify(InviteResponseSchema().dump(invite)), 201


@org_invites_bp.route("", methods=["GET"])
@jwt_required()
def list_invites(organization_id):
    require_organization_role(organization_id, "owner", "manager")
    service = _build_service()
    invites = service.list_pending_invites(organization_id)
    return jsonify(InviteResponseSchema(many=True).dump(invites))


@org_invites_bp.route("/<uuid:invite_id>", methods=["DELETE"])
@jwt_required()
def revoke_invite(organization_id, invite_id):
    require_organization_role(organization_id, "owner", "manager")
    service = _build_service()
    try:
        service.revoke_invite(invite_id, organization_id)
    except InviteNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Invite not found."}}), 404
    return "", 204


@invites_bp.route("/<string:token>", methods=["GET"])
def preview_invite(token):
    service = _build_service()
    try:
        invite = service.get_invite_by_token(token)
    except InviteNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Invite not found."}}), 404
    except InviteExpiredError:
        return jsonify({"error": {"code": "EXPIRED", "message": "This invite has expired."}}), 410
    except InviteAlreadyAcceptedError:
        return jsonify({"error": {"code": "ALREADY_ACCEPTED", "message": "This invite was already accepted."}}), 410

    org = OrganizationRepository().get_by_id(invite.organization_id)
    return jsonify(
        {
            "organization_name": org.name if org else "",
            "role": invite.role,
            "email": invite.email,
            "expires_at": invite.expires_at.isoformat(),
        }
    )


@invites_bp.route("/<string:token>/accept", methods=["POST"])
@jwt_required()
def accept_invite(token):
    accepting_user_id = get_jwt_identity()
    service = _build_service()
    try:
        membership = service.accept_invite(token, accepting_user_id)
    except InviteNotFoundError as err:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(err) or "Invite not found."}}), 404
    except InviteExpiredError:
        return jsonify({"error": {"code": "EXPIRED", "message": "This invite has expired."}}), 410
    except InviteAlreadyAcceptedError:
        return jsonify({"error": {"code": "ALREADY_ACCEPTED", "message": "This invite was already accepted."}}), 410

    return jsonify({"organization_id": str(membership.organization_id), "role": membership.role}), 200
