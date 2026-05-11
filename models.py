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
    isbn: Mapped[str] = mapped_column(String(20), unique=True)


# Pydantic models
class BookIn(BaseModel):
    """Pydantic model for book input"""

    title: str
    author: str
    isbn: str

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN-10 or ISBN-13 format (digits and hyphens, optional X suffix for ISBN-10)."""
        # Strip hyphens and spaces for validation
        stripped = v.replace("-", "").replace(" ", "")
        if re.fullmatch(r"\d{9}[\dX]", stripped) or re.fullmatch(r"\d{13}", stripped):
            return v
        raise ValueError(
            "Invalid ISBN format. Must be a valid ISBN-10 (e.g. 0-306-40615-2) "
            "or ISBN-13 (e.g. 978-3-16-148410-0)."
        )


class BookOut(BaseModel):
    """Pydantic model for book output"""

    id: int
    title: str
    author: str
    isbn: str

    model_config = ConfigDict(from_attributes=True)
