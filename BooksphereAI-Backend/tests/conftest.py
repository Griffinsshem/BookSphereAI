"""
Shared pytest fixtures.

`app` and `db_session` use TestingConfig, which points at
TEST_DATABASE_URL — a SEPARATE database from booksphere_dev, so
running tests never touches (or wipes) your local dev data.
"""
from __future__ import annotations

import pytest

from booksphere.app import create_app
from booksphere.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def db_session(app):
    """Each test runs inside a transaction that's rolled back at the
    end — so tests never leak data into each other, and we don't pay
    the cost of dropping/recreating tables for every single test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    _db.session.bind = connection

    yield _db.session

    _db.session.rollback()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    return app.test_client()
