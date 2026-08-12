"""
Auth Blueprint: thin controllers only.

Every route here follows the same three steps: validate input (schema)
-> call the service -> shape the response. No queries, no password
handling, no token logic happens in this file — that's all in
AuthService. If you find yourself wanting to add an `if` about
business rules here, it belongs in the service instead.
"""
from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from booksphere.api.v1.auth.schemas import (
    AuthResponseSchema,
    LoginRequestSchema,
    MembershipResponseSchema,
    RegisterRequestSchema,
    UserResponseSchema,
)
from booksphere.domain.users.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from booksphere.extensions import limiter
from booksphere.repositories.membership_repository import MembershipRepository
from booksphere.repositories.organization_repository import OrganizationRepository
from booksphere.repositories.refresh_token_repository import RefreshTokenRepository
from booksphere.repositories.user_repository import UserRepository
from booksphere.services.auth.auth_service import AuthService, AuthTokens

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _build_service() -> AuthService:
    return AuthService(
        user_repo=UserRepository(),
        org_repo=OrganizationRepository(),
        membership_repo=MembershipRepository(),
        refresh_token_repo=RefreshTokenRepository(),
    )


def _set_auth_cookies(response, tokens: AuthTokens) -> None:
    """Attaches the refresh token and CSRF token as cookies.

    Centralized here (not duplicated across register/login/refresh)
    so the cookie flags are guaranteed identical everywhere they're
    set — a single place to get SameSite/Secure/httpOnly right.
    """
    response.set_cookie(
        current_app.config["REFRESH_TOKEN_COOKIE_NAME"],
        tokens.raw_refresh_token,
        httponly=True,
        secure=current_app.config["COOKIE_SECURE"],
        samesite=current_app.config["COOKIE_SAMESITE"],
        max_age=int(current_app.config["REFRESH_TOKEN_EXPIRES"].total_seconds()),
        path="/api/v1/auth",
    )
    response.set_cookie(
        current_app.config["CSRF_COOKIE_NAME"],
        tokens.csrf_token,
        httponly=False,
        secure=current_app.config["COOKIE_SECURE"],
        samesite=current_app.config["COOKIE_SAMESITE"],
        max_age=int(current_app.config["REFRESH_TOKEN_EXPIRES"].total_seconds()),
    )


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    schema = RegisterRequestSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    frontend_base_url = request.headers.get("Origin") or "http://localhost:3000"

    service = _build_service()
    try:
        user, organization = service.register(
            email=data["email"],
            password=data["password"],
            full_name=data["full_name"],
            organization_name=data["organization_name"],
            frontend_base_url=frontend_base_url,
        )
    except EmailAlreadyRegisteredError:
        return jsonify({"error": {"code": "EMAIL_TAKEN", "message": "Email already registered."}}), 409

    _, tokens = service.login(data["email"], data["password"])

    response = jsonify(
        AuthResponseSchema().dump({"user": user, "access_token": tokens.access_token})
    )
    _set_auth_cookies(response, tokens)
    return response, 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    schema = LoginRequestSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": err.messages}}), 422

    service = _build_service()
    try:
        user, tokens = service.login(data["email"], data["password"])
    except InvalidCredentialsError:
        return jsonify({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}}), 401

    response = jsonify(
        AuthResponseSchema().dump({"user": user, "access_token": tokens.access_token})
    )
    _set_auth_cookies(response, tokens)
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    raw_refresh_token = request.cookies.get(current_app.config["REFRESH_TOKEN_COOKIE_NAME"])
    if not raw_refresh_token:
        return jsonify({"error": {"code": "NO_REFRESH_TOKEN", "message": "Not authenticated."}}), 401

    service = _build_service()
    try:
        tokens = service.refresh(raw_refresh_token)
    except InvalidRefreshTokenError:
        return jsonify({"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Session expired."}}), 401

    response = jsonify({"access_token": tokens.access_token})
    _set_auth_cookies(response, tokens)
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    raw_refresh_token = request.cookies.get(current_app.config["REFRESH_TOKEN_COOKIE_NAME"])
    if raw_refresh_token:
        _build_service().logout(raw_refresh_token)

    response = jsonify({"message": "Logged out."})
    # Clear both cookies by setting an already-expired max_age.
    response.set_cookie(current_app.config["REFRESH_TOKEN_COOKIE_NAME"], "", max_age=0, path="/api/v1/auth")
    response.set_cookie(current_app.config["CSRF_COOKIE_NAME"], "", max_age=0)
    return response, 200
