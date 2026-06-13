import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db
from models import Base

_SQLITE_URL = "sqlite://"
_SQLITE_KWARGS = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}


def _make_fresh_engine():
    """Return a brand-new in-memory SQLite engine with tables created."""
    engine = create_engine(_SQLITE_URL, **_SQLITE_KWARGS)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped engine for schema-inspection tests only."""
    engine = _make_fresh_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db():
    """Each test gets its own fresh in-memory database for full isolation."""
    engine = _make_fresh_engine()
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture(scope="function")
def test_app():
    """Each test gets its own fresh FastAPI app with a fresh in-memory DB."""
    engine = _make_fresh_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
