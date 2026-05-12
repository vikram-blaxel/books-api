"""Pytest configuration and shared fixtures for the Books API test suite."""

import os

# Set DATABASE_URL before any application modules are imported so that
# dependencies.py does not raise EnvironmentError during test collection.
# The actual test fixtures use their own in-memory SQLite engines, so this
# value is only used for the initial module-level import guard.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db
from models import Base


def _make_memory_engine():
    """Return a fresh in-memory SQLite engine with the schema applied."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped engine used by application-level tests."""
    engine = _make_memory_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db():
    """
    Function-scoped DB session backed by a fresh in-memory SQLite database.

    A new engine (and therefore a new empty database) is created for every
    test function, giving full isolation without relying on savepoint rollback
    semantics that differ between SQLite and PostgreSQL.
    """
    engine = _make_memory_engine()
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def test_app():
    """
    Create a test FastAPI application backed by a fresh in-memory SQLite
    database for each test function.
    """
    engine = _make_memory_engine()

    def override_get_db():
        db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    yield app
    engine.dispose()


@pytest.fixture
def client(test_app):
    """Return a TestClient for the test application."""
    return TestClient(test_app)
