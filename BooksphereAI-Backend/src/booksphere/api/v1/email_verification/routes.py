"""
Email verification Blueprint. /verify-email/<token> is deliberately
PUBLIC (no @jwt_required) -- the token itself is the credential,
matching the same pattern as invite-preview/accept. /resend requires
login, since it acts on "the currently authenticated user's own
account," not an arbitrary target.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from booksphere.domain.users.exceptions import (
    EmailAlreadyVerifiedError,
    VerificationTokenExpiredError,
    VerificationTokenNotFoundError,
)
from booksphere.extensions import limiter
from booksphere.repositories.email_verification_repository import EmailVerificationRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.services.auth.email_verification_service import EmailVerificationService

email_verification_bp = Blueprint(
    "email_verification", __name__, url_prefix="/api/v1/auth"
)


def _build_service() -> EmailVerificationService:
    return EmailVerificationService(EmailVerificationRepository(), UserRepository())


@email_verification_bp.route("/verify-email/<string:token>", methods=["POST"])
def verify_email(token):
    service = _build_service()
    try:
        service.confirm_token(token)
    except VerificationTokenNotFoundError:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Invalid verification link."}}), 404
    except VerificationTokenExpiredError:
        return jsonify({"error": {"code": "EXPIRED", "message": "This verification link has expired."}}), 410

    return jsonify({"message": "Email verified."}), 200


@email_verification_bp.route("/resend-verification", methods=["POST"])
@jwt_required()
@limiter.limit("3 per hour")
def resend_verification():
    user_id = get_jwt_identity()
    frontend_base_url = request.headers.get("Origin") or "http://localhost:3000"

    service = _build_service()
    try:
        service.resend_verification(user_id, frontend_base_url)
    except EmailAlreadyVerifiedError:
        return jsonify({"error": {"code": "ALREADY_VERIFIED", "message": "Your email is already verified."}}), 422

    return jsonify({"message": "Verification email sent."}), 200
