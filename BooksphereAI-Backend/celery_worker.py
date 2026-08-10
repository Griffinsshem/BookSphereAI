"""
Entrypoint for the Celery worker process:
    celery -A celery_worker.celery worker --loglevel=info
"""
from booksphere.app import create_app
from booksphere.tasks.celery_app import celery_app as celery

# create_app() now wires celery_app to this Flask app's config via
# extensions.init_extensions() -> init_celery() -- same as db/migrate/
# jwt. Task modules are imported transitively through the blueprint
# registration chain (invite_routes -> invite_service -> email_tasks),
# so no separate explicit import is needed here anymore.
create_app()
