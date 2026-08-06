"""
Flask extension instances.

Extensions are instantiated once at module scope (uninitialized) and
bound to the app inside init_extensions(), per the Application Factory
Pattern. This avoids circular imports and lets tests create isolated
app instances without state bleeding between them.
"""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

limiter = Limiter(key_func=get_remote_address)

cors = CORS()


def init_extensions(app: Flask) -> None:
    """Bind all Flask extensions to the given app instance."""
    db.init_app(app)

    # Import every model module HERE, immediately after db.init_app,
    # so SQLAlchemy's metadata is always complete -- for the running
    # app AND for `flask db migrate` (which also goes through
    # create_app()). Without this explicit import, a model only
    # becomes visible to Alembic once something else transitively
    # imports it (e.g. its own repository/service/route) -- which is
    # exactly the trap Booking fell into: it had no such chain yet,
    # so `flask db migrate` silently reported "No changes detected"
    # instead of erroring.
    import booksphere.models  # noqa: F401

    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
