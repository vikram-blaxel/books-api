import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db, database_url
from models import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    test_engine = create_engine(database_url)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


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


@pytest.fixture(scope="function")
def test_app(test_engine):
    """Create test FastAPI application with test database.

    Uses a single connection with savepoint-based rollback so that data
    written during a request is visible within the same test function but
    is rolled back at the end of the test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection,
        join_transaction_mode="create_savepoint"
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    yield app

    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
