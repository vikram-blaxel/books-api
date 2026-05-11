from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "978-0-385-08695-0"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "978-0-307-88743-6"},
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
        """Test skip/limit pagination of get_books"""
        create_book(test_db, BookIn(**TEST_BOOKS[0]))
        create_book(test_db, BookIn(**TEST_BOOKS[1]))

        page = get_books(test_db, skip=1, limit=1)
        assert len(page) == 1

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
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="000-0-000-00000-0"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="000-0-000-00000-0")) is None
        assert delete_book(test_db, 999999) is None


# HTTP Router Tests
class TestBookRouter:
    def test_create_book(self, client):
        """Test POST /api/books/ creates a book and returns 201"""
        payload = TEST_BOOKS[0]
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_get_books(self, client):
        """Test GET /api/books/ returns a list"""
        client.post("/api/books/", json=TEST_BOOKS[0])
        client.post("/api/books/", json=TEST_BOOKS[1])
        response = client.get("/api/books/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_books_limit(self, client):
        """Test GET /api/books/ respects limit parameter"""
        client.post("/api/books/", json=TEST_BOOKS[0])
        client.post("/api/books/", json=TEST_BOOKS[1])
        response = client.get("/api/books/?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_book(self, client):
        """Test GET /api/books/{id} returns the correct book"""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book(self, client):
        """Test PUT /api/books/{id} updates and returns the book"""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.put(f"/api/books/{created['id']}", json=TEST_BOOKS[1])
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == TEST_BOOKS[1]["title"]
        assert data["isbn"] == TEST_BOOKS[1]["isbn"]

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for missing book"""
        response = client.put("/api/books/999999", json=TEST_BOOKS[0])
        assert response.status_code == 404

    def test_delete_book(self, client):
        """Test DELETE /api/books/{id} deletes and returns the book"""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]
        # Confirm it is gone
        assert client.get(f"/api/books/{created['id']}").status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404

    def test_create_book_invalid_payload(self, client):
        """Test POST /api/books/ returns 422 for missing required fields"""
        response = client.post("/api/books/", json={"title": "No Author or ISBN"})
        assert response.status_code == 422
