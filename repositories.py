"""Repository layer: database CRUD operations for books."""

from sqlalchemy.orm import Session
import models


def create_book(db: Session, book: models.BookIn) -> models.Book:
    """Create and persist a new book record.

    Args:
        db: Active database session.
        book: Validated input data for the new book.

    Returns:
        The newly created Book ORM instance.
    """
    db_book = models.Book(title=book.title, author=book.author, isbn=book.isbn)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_books(db: Session, skip: int = 0, limit: int = 10) -> list[models.Book]:
    """Return a paginated list of books.

    Args:
        db: Active database session.
        skip: Number of records to skip (offset).
        limit: Maximum number of records to return.

    Returns:
        List of Book ORM instances.
    """
    return db.query(models.Book).offset(skip).limit(limit).all()


def get_book(db: Session, book_id: int) -> models.Book | None:
    """Fetch a single book by primary key.

    Args:
        db: Active database session.
        book_id: Primary key of the book.

    Returns:
        The matching Book ORM instance, or None if not found.
    """
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def update_book(db: Session, book_id: int, book: models.BookIn) -> models.Book | None:
    """Update an existing book record.

    Args:
        db: Active database session.
        book_id: Primary key of the book to update.
        book: Validated input data with updated fields.

    Returns:
        The updated Book ORM instance, or None if not found.
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db_book.title = book.title
        db_book.author = book.author
        db_book.isbn = book.isbn
        db.commit()
        db.refresh(db_book)
        return db_book
    return None


def delete_book(db: Session, book_id: int) -> models.Book | None:
    """Delete a book record by primary key.

    Args:
        db: Active database session.
        book_id: Primary key of the book to delete.

    Returns:
        The deleted Book ORM instance, or None if not found.
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    return None
