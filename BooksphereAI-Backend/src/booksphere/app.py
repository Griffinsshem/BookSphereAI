"""
Application Factory Pattern entrypoint. Stays thin: instantiate,
configure, wire extensions/blueprints/error-handlers/middleware, done.
No business logic here.
"""
from __future__ import annotations

from flask import Flask

from booksphere.config import get_config
from booksphere.extensions import init_extensions


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_middleware(app)

    return app


def _register_blueprints(app: Flask) -> None:
    from booksphere.api.v1 import register_v1_blueprints

    register_v1_blueprints(app)


def _register_error_handlers(app: Flask) -> None:
    from booksphere.api.v1.errors import register_error_handlers

    register_error_handlers(app)


def _register_middleware(app: Flask) -> None:
    from booksphere.security.csrf import register_csrf_protection

    register_csrf_protection(app)
