"""
Shared Celery instance, created ONCE at module import time (like db,
migrate, jwt in extensions.py) -- NOT tied to a specific Flask app
yet. init_celery(app) binds it to a real app's config later, called
from create_app(), same pattern as every other extension.

Why this shape specifically: task modules (email_tasks.py) need to
import `celery_app` to register their @celery_app.task decorators at
import time, but they must NOT trigger create_app() themselves --
doing so previously caused a circular import (email_tasks ->
create_app -> register_blueprints -> invite_routes -> invite_service
-> email_tasks), since create_app() itself imports every blueprint,
which transitively imports every service, which imports this module.
"""
from __future__ import annotations
from celery import Celery, Task

celery_app = Celery("booksphere")


def init_celery(app) -> Celery:
    """Binds the shared celery_app to a real Flask app's config and
    ensures every task runs inside that app's context. Called once,
    from create_app()."""

    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery_app.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]
    celery_app.Task = ContextTask
    return celery_app
