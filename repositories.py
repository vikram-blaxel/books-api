from sqlalchemy.orm import Session
import models


def create_book(db: Session, book: models.BookIn) -> models.Book:
    """Create a new book record in the database."""
    db_book = models.Book(title=book.title, author=book.author, isbn=book.isbn)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_books(db: Session, skip: int = 0, limit: int = 10) -> list[models.Book]:
    """Return a paginated list of all books."""
    return db.query(models.Book).offset(skip).limit(limit).all()


def get_book(db: Session, book_id: int) -> models.Book | None:
    """Return a single book by primary key, or None if not found."""
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def update_book(
    db: Session, book_id: int, book: models.BookIn
) -> models.Book | None:
    """Update an existing book by primary key.

    Returns the updated book, or None if the book does not exist.
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
    """Delete a book by primary key.

    Returns the deleted book object, or None if not found.
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    return None
