"""
CSRF protection for cookie-authenticated endpoints, via the
double-submit cookie pattern.

Why this instead of flask-wtf's CSRF protection: flask-wtf's CSRFProtect
is built around server-rendered forms and Flask sessions. We have
neither — this is a stateless JSON API where only the refresh-token
cookie is session-like. A minimal, purpose-built double-submit check
is simpler and has less surface area than pulling in a
session-oriented library for one narrow use case.

How it works:
1. When we set the refresh_token cookie (login/refresh), we ALSO set a
   csrf_token cookie with a random value — but NOT httpOnly, so
   frontend JS can read it.
2. The frontend reads that cookie and sends its value back in an
   X-CSRF-Token header on any request that relies on the refresh
   cookie (i.e. /auth/refresh, /auth/logout).
3. This middleware checks the header value matches the cookie value.

Why this defeats CSRF: a malicious site can trick a browser into
sending cookies automatically, but it CANNOT read this site's cookies
to put the matching value in a custom header (same-origin policy
blocks that). So a forged cross-site request will have the cookie but
not the matching header — and gets rejected.
"""
from __future__ import annotations

from flask import Flask, current_app, request
from werkzeug.exceptions import Forbidden

_CSRF_PROTECTED_ENDPOINTS = {"auth.refresh", "auth.logout"}


def register_csrf_protection(app: Flask) -> None:
    @app.before_request
    def _check_csrf() -> None:
        if request.endpoint not in _CSRF_PROTECTED_ENDPOINTS:
            return

        cookie_value = request.cookies.get(current_app.config["CSRF_COOKIE_NAME"])
        header_value = request.headers.get("X-CSRF-Token")

        if not cookie_value or not header_value or cookie_value != header_value:
            raise Forbidden(description="CSRF token missing or invalid.")
