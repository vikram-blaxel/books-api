"""Tests for the Books API: repository layer and HTTP router endpoints."""

from sqlalchemy import inspect

from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385086950"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887436"},
]


# ---------------------------------------------------------------------------
# Application-level tests
# ---------------------------------------------------------------------------

class TestMainApp:
    def test_create_app(self, test_app):
        """Test application creation."""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test database initialization."""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------

class TestBookRepository:
    def test_create_book(self, test_db):
        """Test creating a new book."""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.title == TEST_BOOKS[0]["title"]
        assert book.author == TEST_BOOKS[0]["author"]
        assert book.isbn == TEST_BOOKS[0]["isbn"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books."""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books = get_books(test_db)
        assert len(books) == 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test getting a specific book."""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]
        assert retrieved_book.isbn == TEST_BOOKS[0]["isbn"]

    def test_update_book(self, test_db):
        """Test updating a book including its ISBN."""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated_data = BookIn(**TEST_BOOKS[1])
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == TEST_BOOKS[1]["title"]
        assert updated_book.author == TEST_BOOKS[1]["author"]
        assert updated_book.isbn == TEST_BOOKS[1]["isbn"]

    def test_delete_book(self, test_db):
        """Test deleting a book."""
        book = create_book(
            test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001")
        )
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_get(self, test_db):
        """Test get on a nonexistent book returns None."""
        assert get_book(test_db, 999999) is None

    def test_nonexistent_update(self, test_db):
        """Test update on a nonexistent book returns None."""
        assert update_book(
            test_db, 999999, BookIn(title="Test", author="Test", isbn="9780000000002")
        ) is None

    def test_nonexistent_delete(self, test_db):
        """Test delete on a nonexistent book returns None."""
        assert delete_book(test_db, 999999) is None


# ---------------------------------------------------------------------------
# HTTP router (integration) tests
# ---------------------------------------------------------------------------

class TestBookRouter:
    def test_create_book_success(self, client):
        """POST /api/books/ with valid payload returns 201 and the new book."""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_missing_isbn_returns_422(self, client):
        """POST /api/books/ without isbn should return 422 Unprocessable Entity."""
        payload = {"title": "Dune", "author": "Frank Herbert"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_get_books(self, client):
        """GET /api/books/ returns a list of books."""
        client.post(
            "/api/books/",
            json={"title": "Book A", "author": "Author A", "isbn": "9780000000010"},
        )
        client.post(
            "/api/books/",
            json={"title": "Book B", "author": "Author B", "isbn": "9780000000011"},
        )
        response = client.get("/api/books/")
        assert response.status_code == 200
        books = response.json()
        assert isinstance(books, list)
        assert len(books) >= 2

    def test_get_books_pagination(self, client):
        """GET /api/books/?skip=0&limit=1 returns at most one book."""
        client.post(
            "/api/books/",
            json={"title": "Pag A", "author": "Author", "isbn": "9780000000020"},
        )
        client.post(
            "/api/books/",
            json={"title": "Pag B", "author": "Author", "isbn": "9780000000021"},
        )
        response = client.get("/api/books/?skip=0&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_single_book_success(self, client):
        """GET /api/books/{id} returns the correct book."""
        created = client.post(
            "/api/books/",
            json={"title": "Neuromancer", "author": "William Gibson", "isbn": "9780441569595"},
        ).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["isbn"] == "9780441569595"

    def test_get_nonexistent_book_returns_404(self, client):
        """GET /api/books/999999 returns 404."""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_success(self, client):
        """PUT /api/books/{id} updates all fields including isbn."""
        created = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "9780000000030"},
        ).json()
        update_payload = {"title": "New Title", "author": "New Author", "isbn": "9780000000031"}
        response = client.put(f"/api/books/{created['id']}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["isbn"] == "9780000000031"

    def test_update_nonexistent_book_returns_404(self, client):
        """PUT /api/books/999999 returns 404."""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000032"},
        )
        assert response.status_code == 404

    def test_delete_book_success(self, client):
        """DELETE /api/books/{id} removes the book and returns it."""
        created = client.post(
            "/api/books/",
            json={"title": "To Delete", "author": "Author", "isbn": "9780000000040"},
        ).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]
        # Confirm it is gone
        assert client.get(f"/api/books/{created['id']}").status_code == 404

    def test_delete_nonexistent_book_returns_404(self, client):
        """DELETE /api/books/999999 returns 404."""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
