import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import create_app
from dependencies import get_db, database_url
from models import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (session-scoped, used only for schema checks)"""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create an isolated test database session for each test.

    Uses a fresh in-memory SQLite database per test function so that each
    test starts with a clean schema regardless of database backend.
    The session-scoped ``test_engine`` is still used for schema-inspection
    tests (TestMainApp); for repository tests a dedicated per-test engine
    is created so the unique constraints and NOT NULL constraints start
    from a clean state every time.
    """
    # Determine the dialect.  For SQLite we create a fresh per-test
    # in-memory DB; for other dialects we keep the savepoint strategy.
    if test_engine.dialect.name == "sqlite":
        per_test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=per_test_engine)
        db = sessionmaker(autocommit=False, autoflush=False, bind=per_test_engine)()
        try:
            yield db
        finally:
            db.close()
            per_test_engine.dispose()
    else:
        # PostgreSQL / other ACID databases: use the savepoint rollback strategy
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
        db = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)()
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
