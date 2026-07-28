"""
Environment-based configuration.

Secrets (SECRET_KEY, DATABASE_URL, JWT keys) are ALWAYS read from
environment variables. Never hardcoded, never committed, never logged.
"""
from __future__ import annotations

import os
from datetime import timedelta


class BaseConfig:
    """Shared defaults. Do not instantiate directly."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    DEBUG = False
    TESTING = False

    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_TOKEN_LOCATION = ["headers"]

    # --- Rate limiting (flask-limiter) ---
    # Redis-backed so limits are enforced correctly across multiple
    # app instances. Falls back to in-memory only if unset — acceptable
    # for a throwaway local shell, but never for anything shared.
    RATELIMIT_STORAGE_URI: str = os.environ.get(
        "RATELIMIT_STORAGE_URI", "memory://"
    )

    REFRESH_TOKEN_COOKIE_NAME = "bs_refresh_token"
    REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    CSRF_COOKIE_NAME = "bs_csrf_token"

    COOKIE_SAMESITE = "None"
    COOKIE_SECURE = True

   
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    COOKIE_SECURE = False
    COOKIE_SAMESITE = "Lax"
    CORS_ORIGINS = ["http://localhost:3000"]


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://localhost/booksphere_test"
    )
    COOKIE_SECURE = False
    COOKIE_SAMESITE = "Lax"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    # Rate limiting is a cross-cutting concern tested in its own
    # dedicated test (test_rate_limiting.py), not incidentally
    # triggered by unrelated functional tests sharing one session-
    # scoped app instance and IP.
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production must never have DEBUG=True (info disclosure risk)."""


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name: str | None = None) -> type[BaseConfig]:
    """Resolve a config class by name, env var, or safe default.

    Defaults to ProductionConfig when unset — a missing/unknown
    environment should never silently grant DEBUG mode or relaxed
    cookie security.
    """
    name = config_name or os.environ.get("FLASK_ENV", "production")
    return _CONFIG_MAP.get(name, ProductionConfig)
