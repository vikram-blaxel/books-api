from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from pydantic import BaseModel, ConfigDict


# SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all database models"""


class Book(Base):
    """Book model"""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255))
    isbn: Mapped[str] = mapped_column(String(13))


# Pydantic models
class BookIn(BaseModel):
    """Pydantic model for book input"""

    title: str
    author: str
    isbn: str


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
