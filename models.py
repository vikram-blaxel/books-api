import re
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
    isbn: Mapped[str] = mapped_column(String(17), nullable=False)


# Pydantic models
class BookIn(BaseModel):
    """Pydantic model for book input"""

    title: str
    author: str
    isbn: str

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str) -> str:
        """Validate ISBN-10 or ISBN-13 format (digits and hyphens, correct length)."""
        # Strip hyphens for length/digit checks
        digits = value.replace("-", "")
        if not re.fullmatch(r"[0-9X]+", digits, re.IGNORECASE):
            raise ValueError("ISBN must contain only digits, hyphens, or a trailing X")
        if len(digits) not in (10, 13):
            raise ValueError("ISBN must be 10 or 13 digits (excluding hyphens)")
        return value


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
