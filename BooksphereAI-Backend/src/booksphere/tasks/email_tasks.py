"""
Email-sending tasks. Currently LOG the email content instead of
calling a real provider -- see the Team Management feature's
architecture decision.

Imports the SHARED celery_app instance (not tied to a Flask app at
import time) -- this is what breaks the circular import that occurs
if this module tries to build its own Flask app via create_app().
"""
from __future__ import annotations
import logging

from booksphere.tasks.celery_app import celery_app

_logger = logging.getLogger("booksphere.tasks.email")


@celery_app.task(name="booksphere.tasks.send_invite_email")
def send_invite_email(
    to_email: str, organization_name: str, inviter_name: str, accept_url: str
) -> None:
    _logger.info(
        "INVITE_EMAIL to=%s org=%s inviter=%s accept_url=%s",
        to_email,
        organization_name,
        inviter_name,
        accept_url,
    )
