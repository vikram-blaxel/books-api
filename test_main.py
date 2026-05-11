from unittest.mock import patch
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "978-0-385-12167-5"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "978-0-307-88743-6"},
]

# Unique books for the HTTP integration CRUD cycle (avoids ISBN uniqueness conflicts
# with TEST_BOOKS used in other router tests that commit to the shared test DB).
CRUD_BOOKS = [
    {"title": "The Shining", "author": "Stephen King", "isbn": "978-0-385-12168-2"},
    {"title": "Armada", "author": "Ernest Cline", "isbn": "978-0-307-88744-3"},
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

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]

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
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="978-3-16-148410-0"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="978-3-16-148410-0")) is None
        assert delete_book(test_db, 999999) is None


# HTTP Router Tests
class TestBookRoutes:
    def test_create_book_success(self, client):
        """Test POST /api/books/ returns 201 with the created book"""
        payload = TEST_BOOKS[0]
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_invalid_isbn(self, client):
        """Test POST /api/books/ returns 422 for an invalid ISBN"""
        payload = {"title": "Bad ISBN Book", "author": "Someone", "isbn": "not-an-isbn"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_create_book_db_error(self, client):
        """Test POST /api/books/ returns 400 when a database error occurs"""
        with patch("repositories.create_book", side_effect=SQLAlchemyError("db error")):
            response = client.post("/api/books/", json=TEST_BOOKS[0])
        assert response.status_code == 400
        assert "An error occurred creating the book" in response.json()["detail"]

    def test_get_books_success(self, client):
        """Test GET /api/books/ returns 200 with a list"""
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_books_limit_enforced(self, client):
        """Test GET /api/books/ rejects limit > 100"""
        response = client.get("/api/books/?limit=9999")
        assert response.status_code == 422

    def test_get_books_db_error(self, client):
        """Test GET /api/books/ returns 500 when a database error occurs"""
        with patch("repositories.get_books", side_effect=SQLAlchemyError("db error")):
            response = client.get("/api/books/")
        assert response.status_code == 500
        assert "An error occurred retrieving books" in response.json()["detail"]

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for unknown id"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for unknown id"""
        response = client.put("/api/books/999999", json=TEST_BOOKS[0])
        assert response.status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for unknown id"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404

    def test_create_read_update_delete(self, client):
        """Full CRUD cycle through the HTTP layer"""
        # Create using CRUD_BOOKS to avoid ISBN uniqueness conflict with other tests
        create_resp = client.post("/api/books/", json=CRUD_BOOKS[0])
        assert create_resp.status_code == 201
        book_id = create_resp.json()["id"]

        # Read single
        get_resp = client.get(f"/api/books/{book_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["isbn"] == CRUD_BOOKS[0]["isbn"]

        # Update
        update_resp = client.put(f"/api/books/{book_id}", json=CRUD_BOOKS[1])
        assert update_resp.status_code == 200
        assert update_resp.json()["isbn"] == CRUD_BOOKS[1]["isbn"]

        # Delete
        delete_resp = client.delete(f"/api/books/{book_id}")
        assert delete_resp.status_code == 200

        # Confirm gone
        confirm_resp = client.get(f"/api/books/{book_id}")
        assert confirm_resp.status_code == 404
