import re
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from pydantic import BaseModel, ConfigDict, field_validator


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

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN-10 or ISBN-13 format."""
        cleaned = v.replace("-", "").replace(" ", "")
        if not re.fullmatch(r"(?:97[89])?\d{9}[\dX]", cleaned):
            raise ValueError(
                "isbn must be a valid ISBN-10 (10 digits, last may be X) "
                "or ISBN-13 (starts with 978 or 979, 13 digits)"
            )
        return cleaned


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
