"""
API v1 blueprint registry.

Every new resource gets its own Blueprint in its own subpackage.
Register it here, and nowhere else, so app.py never needs to know
about individual resources.
"""
from __future__ import annotations

from flask import Flask


def register_v1_blueprints(app: Flask) -> None:
    from booksphere.api.v1.auth.routes import auth_bp
    from booksphere.api.v1.bookings.routes import bookings_bp
    from booksphere.api.v1.email_verification.routes import email_verification_bp
    from booksphere.api.v1.organizations.routes import organizations_bp
    from booksphere.api.v1.resources.routes import resources_bp
    from booksphere.api.v1.services.routes import services_bp
    from booksphere.api.v1.team.invite_routes import invites_bp, org_invites_bp
    from booksphere.api.v1.team.member_routes import members_bp
    from booksphere.api.v1.users.routes import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(organizations_bp)
    app.register_blueprint(email_verification_bp)
    app.register_blueprint(org_invites_bp)
    app.register_blueprint(invites_bp)
    app.register_blueprint(members_bp)
