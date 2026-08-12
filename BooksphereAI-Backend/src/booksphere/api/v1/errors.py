"""
Centralized error handling for API v1.

Every error response follows one consistent shape:

    { "error": { "code": "...", "message": "..." } }

Internal exception details (stack traces, DB errors) are NEVER
serialized into the response body — only logged server-side. This
prevents stack-trace/info-disclosure leaks to clients.
"""
from __future__ import annotations
import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from booksphere.domain.users.exceptions import EmailNotVerifiedError

_logger = logging.getLogger("booksphere.errors")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(EmailNotVerifiedError)
    def handle_email_not_verified(err: EmailNotVerifiedError):
        # A distinct, recognizable error code -- the frontend
        # specifically checks for EMAIL_NOT_VERIFIED to show the
        # verification prompt rather than a generic error toast.
        return (
            jsonify({"error": {"code": "EMAIL_NOT_VERIFIED", "message": str(err)}}),
            403,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        return (
            jsonify(
                {
                    "error": {
                        "code": err.name.upper().replace(" ", "_"),
                        "message": err.description,
                    }
                }
            ),
            err.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        _logger.exception("Unhandled exception")
        return (
            jsonify(
                {
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                    }
                }
            ),
            500,
        )
