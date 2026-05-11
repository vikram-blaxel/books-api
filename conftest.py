import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Use an in-process SQLite database for all tests so no external Postgres is needed.
TEST_DATABASE_URL = "sqlite:///./test.db"

# Set DATABASE_URL before importing application modules so dependencies.py does not raise.
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

from main import create_app  # noqa: E402  (import after env setup)
from dependencies import get_db  # noqa: E402
from models import Base  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for the test session."""
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    db = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_app(test_engine):
    """Create test FastAPI application with test database override."""

    def override_get_db():
        session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=test_engine
        )
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """Create test HTTP client."""
    return TestClient(test_app)
