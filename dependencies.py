import logging
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from models import Base

logger = logging.getLogger(__name__)

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise EnvironmentError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in your .env file or environment."
    )

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        logger.error("Error initializing the database: %s", e)
        raise


def get_db() -> Generator[Session, None, None]:
    """Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
