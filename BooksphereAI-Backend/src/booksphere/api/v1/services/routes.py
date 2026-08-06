from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.services.schemas import (
    CreateServiceSchema,
    LinkResourceSchema,
    ServiceResponseSchema,
    UpdateServiceSchema,
)
from booksphere.domain.resources.exceptions import (
    CrossTenantResourceLinkError,
    InvalidServiceDurationError,
    ServiceNotFoundError,
)
from booksphere.middleware.tenant_context import require_organization_role
from booksphere.repositories.resource_repository import ResourceRepository
from booksphere.repositories.service_repository import ServiceRepository
from booksphere.repositories.service_resource_repository import ServiceResourceRepository
from booksphere.services.catalog.offering_service import OfferingService

services_bp = Blueprint(
    "services", __name__, url_prefix="/api/v1/organizations/<uuid:organization_id>/services"
)


def _build_service() -> OfferingService:
    return OfferingService(ServiceRepository(), ResourceRepository(), ServiceResourceRepository())


@services_bp.route("", methods=["POST"])
@jwt_required()
def create_service(organization_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = CreateServiceSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        offering = service.create_service(organization_id=organization_id, **data)
    except InvalidServiceDurationError as err:
        return jsonify({"error": {"code": "INVALID_DURATION", "message": str(err)}}), 422

    return jsonify(ServiceResponseSchema().dump(offering)), 201


@services_bp.route("", methods=["GET"])
@jwt_required()
def list_services(organization_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)
    is_active_param = request.args.get("is_active")
    is_active = None if is_active_param is None else is_active_param.lower() == "true"

    repo = ServiceRepository()
    pagination = repo.list_for_organization(
        organization_id, is_active=is_active, page=page, per_page=per_page
    )

    return jsonify(
        {
            "items": ServiceResponseSchema(many=True).dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    )


@services_bp.route("/<uuid:service_id>", methods=["GET"])
@jwt_required()
def get_service(organization_id, service_id):
    require_organization_role(organization_id, "owner", "manager", "staff", "customer")

    service = _build_service()
    try:
        offering = service.get_service(service_id, organization_id)
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404

    return jsonify(ServiceResponseSchema().dump(offering))


@services_bp.route("/<uuid:service_id>", methods=["PATCH"])
@jwt_required()
def update_service(organization_id, service_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = UpdateServiceSchema().load(request.get_json(silent=True) or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        offering = service.update_service(service_id, organization_id, **data)
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404
    except InvalidServiceDurationError as err:
        return jsonify({"error": {"code": "INVALID_DURATION", "message": str(err)}}), 422

    return jsonify(ServiceResponseSchema().dump(offering))


@services_bp.route("/<uuid:service_id>", methods=["DELETE"])
@jwt_required()
def deactivate_service(organization_id, service_id):
    require_organization_role(organization_id, "owner", "manager")

    service = _build_service()
    try:
        service.deactivate_service(service_id, organization_id)
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404

    return "", 204


@services_bp.route("/<uuid:service_id>/resources", methods=["POST"])
@jwt_required()
def link_resource(organization_id, service_id):
    require_organization_role(organization_id, "owner", "manager")

    try:
        data = LinkResourceSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        service.link_resource(service_id, data["resource_id"], organization_id)
    except ServiceNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Service not found."}}), 404
    except CrossTenantResourceLinkError as err:
        return jsonify({"error": {"code": "INVALID_RESOURCE_LINK", "message": str(err)}}), 422

    return "", 201
