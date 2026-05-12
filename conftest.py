import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db
from models import Base


def _make_sqlite_engine():
    """Return a fresh SQLite in-memory engine with the full schema."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (SQLite in-memory for portability)."""
    engine = _make_sqlite_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db():
    """Provide a clean, isolated DB session for each repository test.

    Each test gets its own in-memory SQLite database so there is zero
    state leakage between tests regardless of what the repository commits.
    """
    engine = _make_sqlite_engine()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def test_app():
    """Create a test FastAPI application backed by a fresh in-memory SQLite DB."""
    engine = _make_sqlite_engine()

    def override_get_db():
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
