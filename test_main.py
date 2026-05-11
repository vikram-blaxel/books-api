from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect
import pytest


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533485"},
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

    def test_books_table_has_isbn_column(self, test_engine):
        """Test that the books table includes the isbn column"""
        inspector = inspect(test_engine)
        columns = {col["name"] for col in inspector.get_columns("books")}
        assert "isbn" in columns, "isbn column must exist in books table"

    def test_isbn_column_is_not_nullable(self, test_engine):
        """Test that the isbn column enforces NOT NULL"""
        inspector = inspect(test_engine)
        columns = {col["name"]: col for col in inspector.get_columns("books")}
        assert columns["isbn"]["nullable"] is False, "isbn column must be NOT NULL"


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
        #assert len(books) >= 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

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
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780000000002")) is None
        assert delete_book(test_db, 999999) is None

    # --- ISBN-specific tests added for PR #24 ---

    def test_isbn_is_stored_and_returned(self, test_db):
        """Test that isbn is persisted and returned correctly on create"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.isbn == TEST_BOOKS[0]["isbn"], "isbn must be stored and returned by create_book"

    def test_isbn_is_returned_on_get(self, test_db):
        """Test that isbn is present when retrieving a single book"""
        created = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        fetched = get_book(test_db, created.id)
        assert fetched is not None
        assert fetched.isbn == TEST_BOOKS[0]["isbn"]

    def test_isbn_is_updated_on_update(self, test_db):
        """Test that isbn is updated when update_book is called"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated = update_book(test_db, book.id, BookIn(**TEST_BOOKS[1]))
        assert updated is not None
        assert updated.isbn == TEST_BOOKS[1]["isbn"], "isbn must be updated when calling update_book"

    def test_isbn_is_required(self, test_db):
        """Test that omitting isbn raises a validation error (Pydantic level)"""
        with pytest.raises(Exception):
            BookIn(title="No ISBN Book", author="Some Author")

    def test_isbn_uniqueness_enforced(self, test_db):
        """Test that inserting two books with the same ISBN is rejected by the DB"""
        create_book(test_db, BookIn(**TEST_BOOKS[0]))
        with pytest.raises(Exception):
            # Same isbn — must violate the unique constraint
            create_book(
                test_db,
                BookIn(title="Duplicate ISBN", author="Another Author", isbn=TEST_BOOKS[0]["isbn"]),
            )


# HTTP API Tests (via test client)
class TestBooksAPI:
    def test_create_book_endpoint_returns_isbn(self, client):
        """POST /api/books/ must include isbn in the response body"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441172719"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["isbn"] == payload["isbn"]

    def test_get_book_endpoint_returns_isbn(self, client):
        """GET /api/books/{id} must return isbn"""
        payload = {"title": "1984", "author": "George Orwell", "isbn": "9780451524935"}
        create_resp = client.post("/api/books/", json=payload)
        assert create_resp.status_code == 201
        book_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/books/{book_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["isbn"] == payload["isbn"]

    def test_list_books_endpoint_returns_isbn(self, client):
        """GET /api/books/ must include isbn in each returned book"""
        payload = {"title": "Brave New World", "author": "Aldous Huxley", "isbn": "9780060850524"}
        client.post("/api/books/", json=payload)
        response = client.get("/api/books/")
        assert response.status_code == 200
        books = response.json()
        assert len(books) >= 1
        assert all("isbn" in b for b in books)

    def test_create_book_without_isbn_returns_422(self, client):
        """POST /api/books/ without isbn must be rejected with HTTP 422"""
        payload = {"title": "Missing ISBN", "author": "Ghost Writer"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_update_book_endpoint_updates_isbn(self, client):
        """PUT /api/books/{id} must update isbn"""
        original = {"title": "Old Title", "author": "Old Author", "isbn": "9780000111111"}
        create_resp = client.post("/api/books/", json=original)
        assert create_resp.status_code == 201
        book_id = create_resp.json()["id"]

        updated = {"title": "New Title", "author": "New Author", "isbn": "9780000222222"}
        put_resp = client.put(f"/api/books/{book_id}", json=updated)
        assert put_resp.status_code == 200
        assert put_resp.json()["isbn"] == updated["isbn"]

    def test_get_nonexistent_book_returns_404(self, client):
        """GET /api/books/999999 must return 404"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_nonexistent_book_returns_404(self, client):
        """PUT /api/books/999999 must return 404"""
        payload = {"title": "Ghost", "author": "Nobody", "isbn": "9780000999999"}
        response = client.put("/api/books/999999", json=payload)
        assert response.status_code == 404

    def test_delete_nonexistent_book_returns_404(self, client):
        """DELETE /api/books/999999 must return 404"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
