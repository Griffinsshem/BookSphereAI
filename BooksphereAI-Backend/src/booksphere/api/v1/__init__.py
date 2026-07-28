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
    from booksphere.api.v1.users.routes import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
