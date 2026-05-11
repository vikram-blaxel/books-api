import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    try:
        return repositories.create_book(db=db, book=book)
    except Exception as e:
        logger.exception("Error creating book")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create book.",
        ) from e


@router.get(
    "/books/", response_model=List[models.BookOut], status_code=status.HTTP_200_OK
)
def get_books(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return repositories.get_books(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.exception("Error retrieving books")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve books.",
        ) from e


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
