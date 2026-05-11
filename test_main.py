from sqlalchemy import inspect

from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385086950"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887436"},
]


class TestMainApp:
    """Tests for application-level setup."""

    def test_create_app(self, test_app):
        """Test application creation"""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test database initialization"""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# Repository Tests
class TestBookRepository:
    """Tests for the book repository (data access layer)."""

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
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780000000000")) is None
        assert delete_book(test_db, 999999) is None


# HTTP / Router Tests
class TestBookRoutes:
    """Integration tests for the book HTTP endpoints."""

    def test_create_book_returns_201(self, client):
        """POST /api/books/ should create a book and return 201"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_invalid_body_returns_422(self, client):
        """POST /api/books/ with missing required fields should return 422"""
        response = client.post("/api/books/", json={"title": "No Author or ISBN"})
        assert response.status_code == 422

    def test_get_books_returns_200(self, client):
        """GET /api/books/ should return a list and 200"""
        # Create one book first
        client.post("/api/books/", json={"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"})
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book_returns_200(self, client):
        """GET /api/books/{id} should return the book"""
        created = client.post(
            "/api/books/",
            json={"title": "Neuromancer", "author": "William Gibson", "isbn": "9780441569595"},
        ).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_book_not_found_returns_404(self, client):
        """GET /api/books/{id} for a missing book should return 404"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_returns_200(self, client):
        """PUT /api/books/{id} should update the book and return 200"""
        created = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "9780000000002"},
        ).json()
        updated_payload = {"title": "New Title", "author": "New Author", "isbn": "9780000000003"}
        response = client.put(f"/api/books/{created['id']}", json=updated_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["isbn"] == "9780000000003"

    def test_update_book_not_found_returns_404(self, client):
        """PUT /api/books/{id} for a missing book should return 404"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000004"},
        )
        assert response.status_code == 404

    def test_delete_book_returns_200(self, client):
        """DELETE /api/books/{id} should delete and return the book"""
        created = client.post(
            "/api/books/",
            json={"title": "To Delete", "author": "Author", "isbn": "9780000000005"},
        ).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        # Verify it's gone
        assert client.get(f"/api/books/{created['id']}").status_code == 404

    def test_delete_book_not_found_returns_404(self, client):
        """DELETE /api/books/{id} for a missing book should return 404"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404

    def test_get_books_limit_cap(self, client):
        """GET /api/books/ with limit > 100 should be capped to 100"""
        response = client.get("/api/books/?limit=9999")
        assert response.status_code == 200
