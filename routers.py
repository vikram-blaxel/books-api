import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import repositories
from dependencies import get_db

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter()


@router.post(
    "/books/", response_model=models.BookOut, status_code=status.HTTP_201_CREATED
)
def create_book(book: models.BookIn, db: Session = Depends(get_db)):
    """Create a new book."""
    try:
        return repositories.create_book(db=db, book=book)
    except IntegrityError as e:
        logger.error("IntegrityError creating book: %s", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with the provided data already exists or violates a constraint.",
        ) from e
    except Exception as e:
        logger.error("Unexpected error creating book: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred while processing your request.",
        ) from e


@router.get(
    "/books/", response_model=List[models.BookOut], status_code=status.HTTP_200_OK
)
def get_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Return a paginated list of books."""
    try:
        return repositories.get_books(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error("Unexpected error fetching books: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request.",
        ) from e


@router.get(
    "/books/{book_id}", response_model=models.BookOut, status_code=status.HTTP_200_OK
)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Return a single book by ID."""
    db_book = repositories.get_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return db_book


@router.put(
    "/books/{book_id}", response_model=models.BookOut, status_code=status.HTTP_200_OK
)
def update_book(book_id: int, book: models.BookIn, db: Session = Depends(get_db)):
    """Update an existing book by ID."""
    db_book = repositories.update_book(db=db, book_id=book_id, book=book)
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return db_book


@router.delete(
    "/books/{book_id}", response_model=models.BookOut, status_code=status.HTTP_200_OK
)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book by ID."""
    db_book = repositories.delete_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return db_book
