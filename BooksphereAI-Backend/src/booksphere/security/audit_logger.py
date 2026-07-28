"""
Structured audit logging for security-relevant events.

Uses Python's standard logging, configured to emit structured
(single-line, key=value) records rather than free-text — this is what
makes it possible to grep/query these logs later without parsing
prose. A dedicated "security" logger name lets these be routed
differently (e.g., to a SIEM) from general application logs later.
"""
from __future__ import annotations

import logging

_logger = logging.getLogger("booksphere.security")


def log_security_event(event: str, **context: object) -> None:
    """Log a security-relevant event with structured context.

    Never pass raw secrets (passwords, tokens) as context values —
    only identifiers (user_id, email, ip) that are safe to persist in
    logs.
    """
    details = " ".join(f"{key}={value}" for key, value in context.items())
    _logger.info("%s %s", event, details)
