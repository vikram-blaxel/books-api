from sqlalchemy import inspect

from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# Test data constants — unique ISBNs per test to avoid UNIQUE constraint
# collisions when the savepoint rollback mechanism is used with SQLite.
TEST_BOOK_1 = {"title": "Carrie", "author": "Stephen King", "isbn": "9780385121682"}
TEST_BOOK_2 = {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887443"}


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
        book_data = {"title": "Carrie", "author": "Stephen King", "isbn": "9780001000001"}
        book = create_book(test_db, BookIn(**book_data))
        assert book.title == book_data["title"]
        assert book.author == book_data["author"]
        assert book.isbn == book_data["isbn"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books"""
        book1 = create_book(test_db, BookIn(title="Book One", author="Author A", isbn="9780001000002"))
        book2 = create_book(test_db, BookIn(title="Book Two", author="Author B", isbn="9780001000003"))

        books = get_books(test_db)
        assert len(books) >= 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(title="Carrie", author="Stephen King", isbn="9780001000004"))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == created_book.title
        assert retrieved_book.isbn == created_book.isbn

    def test_update_book(self, test_db):
        """Test updating a book"""
        book = create_book(test_db, BookIn(title="Old Title", author="Old Author", isbn="9780001000005"))
        updated_data = BookIn(title="New Title", author="New Author", isbn="9780001000006")
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == updated_data.title
        assert updated_book.author == updated_data.author
        assert updated_book.isbn == updated_data.isbn

    def test_delete_book(self, test_db):
        """Test deleting a book"""
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="9780001000007"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780001000008")) is None
        assert delete_book(test_db, 999999) is None


# HTTP Router Tests
class TestBookRouter:
    def test_create_book(self, client):
        """Test POST /api/books/ creates a book and returns isbn in response"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_get_books(self, client):
        """Test GET /api/books/ returns a list"""
        client.post("/api/books/", json={"title": "Book A", "author": "Author A", "isbn": "9780002000010"})
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book(self, client):
        """Test GET /api/books/{id} returns the correct book"""
        created = client.post(
            "/api/books/", json={"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357"}
        ).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["isbn"] == "9780553293357"

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book(self, client):
        """Test PUT /api/books/{id} updates isbn correctly"""
        created = client.post(
            "/api/books/", json={"title": "Old Title", "author": "Old Author", "isbn": "9780002000020"}
        ).json()
        updated_payload = {"title": "New Title", "author": "New Author", "isbn": "9780002000021"}
        response = client.put(f"/api/books/{created['id']}", json=updated_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["isbn"] == "9780002000021"

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for missing book"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780002000030"},
        )
        assert response.status_code == 404

    def test_delete_book(self, client):
        """Test DELETE /api/books/{id} removes the book"""
        created = client.post(
            "/api/books/", json={"title": "To Delete", "author": "Author", "isbn": "9780002000040"}
        ).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert client.get(f"/api/books/{created['id']}").status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404

    def test_get_books_limit_bounded(self, client):
        """Test GET /api/books/ rejects limit > 100"""
        response = client.get("/api/books/?limit=10000000")
        assert response.status_code == 422
