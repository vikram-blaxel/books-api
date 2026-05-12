from sqlalchemy.orm import Session
import models


# Create a new book
def create_book(db: Session, book: models.BookIn):
    """Create and persist a new book record."""
    db_book = models.Book(title=book.title, author=book.author, isbn=book.isbn)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


# Get all books
def get_books(db: Session, skip: int = 0, limit: int = 10):
    """Return a paginated list of books."""
    return db.query(models.Book).offset(skip).limit(limit).all()


# Get a book by ID
def get_book(db: Session, book_id: int):
    """Return a single book by its ID, or None if not found."""
    return db.query(models.Book).filter(models.Book.id == book_id).first()


# Update a book
def update_book(db: Session, book_id: int, book: models.BookIn):
    """Update an existing book's fields; returns None if not found."""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db_book.title = book.title
        db_book.author = book.author
        db_book.isbn = book.isbn
        db.commit()
        db.refresh(db_book)
        return db_book
    return None


# Delete a book
def delete_book(db: Session, book_id: int):
    """Delete a book by ID; returns the deleted object or None if not found."""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    return None
