import os

# Set a default DATABASE_URL for tests when one is not already provided.
# This allows the test suite to run without a live PostgreSQL instance
# by falling back to an in-process SQLite database.
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402, F401
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import create_app  # noqa: E402
from dependencies import get_db  # noqa: E402
from models import Base  # noqa: E402

_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        _DATABASE_URL,
        connect_args={"check_same_thread": False}
        if _DATABASE_URL.startswith("sqlite")
        else {},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session that rolls back after each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    db = sessionmaker(
        autocommit=False, autoflush=False, bind=connection,
        join_transaction_mode="create_savepoint"
    )()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_app(test_engine):
    """Create test FastAPI application with test database"""

    def override_get_db():
        connection = test_engine.connect()
        transaction = connection.begin()
        db = sessionmaker(
            autocommit=False, autoflush=False, bind=connection,
            join_transaction_mode="create_savepoint"
        )()
        try:
            yield db
        finally:
            db.close()
            transaction.rollback()
            connection.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
