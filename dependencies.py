from typing import Generator
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise EnvironmentError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in your .env file or environment."
    )

# Create engine only if not in test mode
# Engine creation is deferred - only created when needed
engine = None
SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        engine = create_engine(database_url)
    return engine


def get_session_local():
    """Get or create the session local."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal


def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=get_engine())
    except SQLAlchemyError as e:
        print(f"Error initializing the database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """Dependency for database sessions."""
    session_local = get_session_local()
    db = session_local()
    try:
        yield db
    finally:
        db.close()
