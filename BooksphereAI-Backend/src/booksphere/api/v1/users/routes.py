"""Users Blueprint: currently just /me."""
from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from booksphere.api.v1.auth.schemas import (
    MembershipResponseSchema,
    UserResponseSchema,
)
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.repositories.user_repository import UserRepository

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = UserRepository().get_by_id(user_id)
    memberships = MembershipRepository().list_for_user(user_id)

    return jsonify(
        {
            "user": UserResponseSchema().dump(user),
            "memberships": MembershipResponseSchema(many=True).dump(memberships),
        }
    )
