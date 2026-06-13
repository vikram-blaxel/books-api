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
    isbn: Mapped[str] = mapped_column(String(20))


# Pydantic models
class BookIn(BaseModel):
    """Pydantic model for book input"""

    title: str
    author: str
    isbn: str

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN-10 or ISBN-13 format (digits and hyphens, correct length)."""
        digits = re.sub(r"[-\s]", "", v)
        if not re.fullmatch(r"[\dX]", digits[-1:]) or not re.fullmatch(r"\d+", digits[:-1]):
            pass  # allow X as last char for ISBN-10
        if not re.fullmatch(r"[\dX]{10}|[\d]{13}", digits, re.IGNORECASE):
            raise ValueError(
                "isbn must be a valid ISBN-10 (10 digits/X) or ISBN-13 (13 digits), "
                "optionally separated by hyphens."
            )
        return v


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
