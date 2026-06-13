from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from pydantic import BaseModel, ConfigDict, field_validator
import re


# SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all database models"""


class Book(Base):
    """Book model"""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255))
    isbn: Mapped[str] = mapped_column(String(13), unique=True)


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
        if re.match(r"^\d{9}[\dX]$", cleaned) or re.match(r"^\d{13}$", cleaned):
            return cleaned
        raise ValueError(
            "Invalid ISBN format. Must be ISBN-10 (e.g. 0306406152) "
            "or ISBN-13 (e.g. 9780306406157)."
        )


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
