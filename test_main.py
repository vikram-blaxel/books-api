import pytest
from sqlalchemy import inspect
from fastapi import status
from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# Test data constants — include isbn field (valid ISBN-13 values)
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533225"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887436"},
]


class TestMainApp:
    def test_create_app(self, test_app):
        """Test application creation"""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test database initialization"""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# Repository Tests
class TestBookRepository:
    def test_create_book(self, test_db):
        """Test creating a new book"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.title == TEST_BOOKS[0]["title"]
        assert book.author == TEST_BOOKS[0]["author"]
        assert book.isbn == TEST_BOOKS[0]["isbn"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books"""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books = get_books(test_db)
        assert len(books) >= 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_books_pagination(self, test_db):
        """Test pagination parameters (skip / limit) in get_books"""
        create_book(test_db, BookIn(**TEST_BOOKS[0]))
        create_book(test_db, BookIn(**TEST_BOOKS[1]))

        # limit=1 should return exactly one book
        books = get_books(test_db, skip=0, limit=1)
        assert len(books) == 1

        # skip=1, limit=1 should return the second book only
        all_books = get_books(test_db)
        books_skipped = get_books(test_db, skip=1, limit=1)
        assert len(books_skipped) == 1
        assert books_skipped[0].id != books[0].id

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]
        assert retrieved_book.isbn == TEST_BOOKS[0]["isbn"]

    def test_update_book(self, test_db):
        """Test updating a book"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated_data = BookIn(**TEST_BOOKS[1])
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == TEST_BOOKS[1]["title"]
        assert updated_book.author == TEST_BOOKS[1]["author"]
        assert updated_book.isbn == TEST_BOOKS[1]["isbn"]

    def test_delete_book(self, test_db):
        """Test deleting a book"""
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="9780307887436"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780307887436")) is None
        assert delete_book(test_db, 999999) is None


# ISBN validation tests
class TestIsbnValidation:
    def test_valid_isbn13(self):
        """BookIn accepts a valid ISBN-13"""
        book = BookIn(title="T", author="A", isbn="9780385533225")
        assert book.isbn == "9780385533225"

    def test_valid_isbn13_with_hyphens(self):
        """BookIn accepts a hyphenated ISBN-13"""
        book = BookIn(title="T", author="A", isbn="978-0-385-53322-5")
        assert book.isbn == "978-0-385-53322-5"

    def test_valid_isbn10(self):
        """BookIn accepts a valid ISBN-10"""
        book = BookIn(title="T", author="A", isbn="0306406152")
        assert book.isbn == "0306406152"

    def test_invalid_isbn_too_short(self):
        """BookIn rejects an ISBN that is too short"""
        with pytest.raises(Exception):
            BookIn(title="T", author="A", isbn="12345")

    def test_invalid_isbn_too_long(self):
        """BookIn rejects an ISBN that is too long"""
        with pytest.raises(Exception):
            BookIn(title="T", author="A", isbn="12345678901234")

    def test_invalid_isbn_non_numeric(self):
        """BookIn rejects an ISBN with invalid characters"""
        with pytest.raises(Exception):
            BookIn(title="T", author="A", isbn="97803854HELLO")


# Router / HTTP integration tests
class TestBookRoutes:
    def test_create_book_returns_201(self, client):
        """POST /api/books/ with valid payload returns 201 and the created book"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_missing_isbn_returns_422(self, client):
        """POST /api/books/ without isbn returns 422 Unprocessable Entity"""
        payload = {"title": "Dune", "author": "Frank Herbert"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_create_book_invalid_isbn_returns_422(self, client):
        """POST /api/books/ with an invalid isbn returns 422"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "NOTANISBN"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_get_books_returns_200(self, client):
        """GET /api/books/ returns 200 and a list"""
        response = client.get("/api/books/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_books_limit_cap(self, client):
        """GET /api/books/ with limit > 100 returns 422"""
        response = client.get("/api/books/?limit=10000000")
        assert response.status_code == 422

    def test_get_book_not_found_returns_404(self, client):
        """GET /api/books/{id} for unknown id returns 404"""
        response = client.get("/api/books/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_book_returns_isbn(self, client):
        """GET /api/books/{id} response includes isbn field"""
        payload = {"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357"}
        created = client.post("/api/books/", json=payload).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["isbn"] == payload["isbn"]

    def test_update_book_returns_updated_data(self, client):
        """PUT /api/books/{id} updates and returns the book"""
        payload = {"title": "Old Title", "author": "Old Author", "isbn": "9780385533225"}
        created = client.post("/api/books/", json=payload).json()
        update_payload = {"title": "New Title", "author": "New Author", "isbn": "9780441013593"}
        response = client.put(f"/api/books/{created['id']}", json=update_payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Title"
        assert data["isbn"] == "9780441013593"

    def test_update_book_not_found_returns_404(self, client):
        """PUT /api/books/{id} for unknown id returns 404"""
        payload = {"title": "T", "author": "A", "isbn": "9780385533225"}
        response = client.put("/api/books/999999", json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_book_returns_deleted_book(self, client):
        """DELETE /api/books/{id} returns the deleted book"""
        payload = {"title": "To Delete", "author": "Author", "isbn": "9780441013593"}
        created = client.post("/api/books/", json=payload).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == created["id"]

    def test_delete_book_not_found_returns_404(self, client):
        """DELETE /api/books/{id} for unknown id returns 404"""
        response = client.delete("/api/books/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
