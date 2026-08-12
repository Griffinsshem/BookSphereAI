"""
Resources Blueprint. Every route: validate input -> check
authorization via require_organization_role -> call ResourceService
-> shape response. No business logic here.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.resources.schemas import (
    CreateResourceSchema,
    CreateWorkingHoursSchema,
    ResourceResponseSchema,
    UpdateResourceSchema,
    WorkingHoursResponseSchema,
)
from booksphere.domain.resources.exceptions import (
    InvalidResourceTypeError,
    InvalidWorkingHoursError,
    ResourceNotFoundError,
)
from booksphere.middleware.tenant_context import require_organization_role, require_verified_email
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.working_hours_repository import WorkingHoursRepository
from booksphere.services.catalog.resource_service import ResourceService

resources_bp = Blueprint(
    "resources", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>/resources"
)


def _build_service() -> ResourceService:
    return ResourceService(ResourceRepository(), WorkingHoursRepository())


@resources_bp.route("", methods=["POST"])
@jwt_required()
def create_resource(organization_id):
    require_organization_role(organization_id, "owner", "manager")
    require_verified_email()

    try:
        data = CreateResourceSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        resource = service.create_resource(organization_id=organization_id, **data)
    except InvalidResourceTypeError as err:
        return jsonify({"error": {"code": "INVALID_RESOURCE_TYPE", "message": str(err)}}), 422

    return jsonify(ResourceResponseSchema().dump(resource)), 201


@resources_bp.route("", methods=["GET"])
@jwt_required()
def list_resources(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)
    resource_type = request.args.get("resource_type")
    is_active_param = request.args.get("is_active")
    is_active = None if is_active_param is None else is_active_param.lower() == "true"

    repo = ResourceRepository()
    pagination = repo.list_for_organization(
        organization_id, resource_type=resource_type, is_active=is_active, page=page, per_page=per_page
    )

    return jsonify(
        {
            "items": ResourceResponseSchema(many=True).dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    )


@resources_bp.route("/<uuid:resource_id>", methods=["GET"])
@jwt_required()
def get_resource(organization_id, resource_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    service = _build_service()
    try:
        resource = service.get_resource(resource_id, organization_id)
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404

    return jsonify(ResourceResponseSchema().dump(resource))


@resources_bp.route("/<uuid:resource_id>", methods=["PATCH"])
@jwt_required()
def update_resource(organization_id, resource_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = UpdateResourceSchema().load(request.get_json(silent=True) or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        resource = service.update_resource(resource_id, organization_id, **data)
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404

    return jsonify(ResourceResponseSchema().dump(resource))


@resources_bp.route("/<uuid:resource_id>", methods=["DELETE"])
@jwt_required()
def deactivate_resource(organization_id, resource_id):
    require_organization_role(organization_id, "owner", "manager")

    service = _build_service()
    try:
        service.deactivate_resource(resource_id, organization_id)
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404

    return "", 204


@resources_bp.route("/<uuid:resource_id>/working-hours", methods=["POST"])
@jwt_required()
def add_working_hours(organization_id, resource_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = CreateWorkingHoursSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        window = service.add_working_hours(resource_id=resource_id, organization_id=organization_id, **data)
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404
    except InvalidWorkingHoursError as err:
        return jsonify({"error": {"code": "INVALID_WORKING_HOURS", "message": str(err)}}), 422

    return jsonify(WorkingHoursResponseSchema().dump(window)), 201


@resources_bp.route("/<uuid:resource_id>/working-hours", methods=["GET"])
@jwt_required()
def list_working_hours(organization_id, resource_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    service = _build_service()
    try:
        windows = service.list_working_hours(resource_id, organization_id)
    except ResourceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found."}}), 404

    return jsonify(WorkingHoursResponseSchema(many=True).dump(windows))
