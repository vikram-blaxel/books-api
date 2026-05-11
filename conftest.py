import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import create_app
from dependencies import get_db, database_url
from models import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session that rolls back after each test"""
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
def test_app(test_db):
    """Create test FastAPI application with test database using transactional rollback"""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # session lifecycle managed by test_db fixture

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
