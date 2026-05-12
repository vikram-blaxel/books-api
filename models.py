import re
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from pydantic import BaseModel, ConfigDict, field_validator


# SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


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

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN-10 or ISBN-13 format."""
        if not re.match(r"^(?:\d{9}[\dX]|\d{13})$", v):
            raise ValueError(
                "isbn must be a valid ISBN-10 (9 digits + digit or X) "
                "or ISBN-13 (13 digits)"
            )
        return v


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
