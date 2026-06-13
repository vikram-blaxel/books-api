import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db
from models import Base


def _make_memory_engine():
    """Create a fresh in-memory SQLite engine with a single shared connection."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_engine():
    """Fresh in-memory SQLite engine per test — guarantees isolation."""
    engine = _make_memory_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    db = sessionmaker(
        autocommit=False, autoflush=False, bind=connection,
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def test_app():
    """Create test FastAPI application with a fresh in-memory database per test."""
    engine = _make_memory_engine()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    yield app

    engine.dispose()


@pytest.fixture(scope="function")
def client(test_app):
    """Create test client."""
    return TestClient(test_app)
