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
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
