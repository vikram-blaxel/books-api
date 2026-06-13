import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List
import models
import repositories
from dependencies import get_db

logger = logging.getLogger(__name__)

# Router for /books endpoints (mounted under /api in main.py)
router = APIRouter()


@router.post(
    "/books/", response_model=models.BookOut, status_code=status.HTTP_201_CREATED
)
def create_book(book: models.BookIn, db: Session = Depends(get_db)):
    try:
        return repositories.create_book(db=db, book=book)
    except IntegrityError as e:
        logger.exception("IntegrityError creating book: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create book. A book with that ISBN may already exist.",
        )
    except SQLAlchemyError as e:
        logger.exception("Database error creating book: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create book.",
        )


@router.get(
    "/books/", response_model=List[models.BookOut], status_code=status.HTTP_200_OK
)
def get_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        return repositories.get_books(db=db, skip=skip, limit=limit)
    except SQLAlchemyError as e:
        logger.exception("Database error fetching books: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve books.",
        )


@router.get(
    "/books/{book_id}", response_model=models.BookOut, status_code=status.HTTP_200_OK
)
def get_book(book_id: int, db: Session = Depends(get_db)):
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
    db_book = repositories.delete_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return db_book
