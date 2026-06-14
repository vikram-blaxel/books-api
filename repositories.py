from sqlalchemy.orm import Session
import models

_MAX_LIMIT = 100


# Create a new book
def create_book(db: Session, book: models.BookIn):
    """Create and persist a new Book record."""
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


# Get all books
def get_books(db: Session, skip: int = 0, limit: int = 10):
    """Return a paginated list of books (hard-capped at 100 per request)."""
    limit = min(limit, _MAX_LIMIT)
    return db.query(models.Book).offset(skip).limit(limit).all()


# Get a book by ID
def get_book(db: Session, book_id: int):
    """Return a single Book by primary key, or None if not found."""
    return db.query(models.Book).filter(models.Book.id == book_id).first()


# Update a book
def update_book(db: Session, book_id: int, book: models.BookIn):
    """Update an existing Book record; returns None if not found."""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        for field, value in book.model_dump().items():
            setattr(db_book, field, value)
        db.commit()
        db.refresh(db_book)
        return db_book
    return None


# Delete a book
def delete_book(db: Session, book_id: int):
    """Delete a Book record; returns the deleted object or None if not found."""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    return None
